import Foundation
import CSQLite

public struct NoteError: LocalizedError {
    public let message: String
    public init(_ message: String) { self.message = message }
    public var errorDescription: String? { message }
}
public struct Todo: Identifiable, Codable, Equatable {
    public let id: String
    public let title: String
    public let day: String
    public let done: Bool
    public let completedAt: String?
    public let projectID: String?
    public let ruleID: String?
}
public struct Project: Identifiable, Codable, Equatable {
    public let id: String
    public let name: String
    public let goal: String
    public let progress: Int
    public let nextAction: String
}
public struct DailyRule: Identifiable, Codable, Equatable {
    public let id: String
    public let title: String
    public let active: Bool
}
public final class Store {
    private var db: OpaquePointer?
    public let path: String
    public static var defaultPath: String {
        FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("DailyTaskNote/tasks.sqlite3").path
    }
    public static func day(_ date: Date = Date()) -> String {
        let f = DateFormatter(); f.locale = Locale(identifier: "en_US_POSIX")
        f.calendar = Calendar(identifier: .gregorian); f.timeZone = .current; f.dateFormat = "yyyy-MM-dd"
        return f.string(from: date)
    }
    public static func validateDay(_ value: String) throws {
        let f = DateFormatter(); f.locale = Locale(identifier: "en_US_POSIX")
        f.calendar = Calendar(identifier: .gregorian); f.dateFormat = "yyyy-MM-dd"; f.isLenient = false
        guard value.count == 10, let d = f.date(from: value), f.string(from: d) == value else { throw NoteError("日期应为 YYYY-MM-DD。") }
    }
    public init(path: String = Store.defaultPath) throws {
        self.path = path
        try FileManager.default.createDirectory(at: URL(fileURLWithPath: path).deletingLastPathComponent(), withIntermediateDirectories: true)
        guard sqlite3_open_v2(path, &db, SQLITE_OPEN_READWRITE | SQLITE_OPEN_CREATE | SQLITE_OPEN_FULLMUTEX, nil) == SQLITE_OK else {
            let error = db.map { String(cString: sqlite3_errmsg($0)) } ?? "无法打开文件"
            if let db { sqlite3_close(db) }; db = nil
            throw NoteError("无法打开数据库，原文件未被替换：\(error)")
        }
        do {
            sqlite3_busy_timeout(db, 2500)
            guard try query("PRAGMA quick_check").first?["quick_check"] == "ok" else { throw NoteError("数据库检查失败，原文件已保留，请先备份再修复。") }
            let version = Int(try query("PRAGMA user_version").first?["user_version"] ?? "0") ?? 0
            guard version <= 1 else { throw NoteError("数据库来自较新版本，请更新程序；原数据已保留。") }
            try execute("PRAGMA journal_mode=WAL")
            try execute("PRAGMA foreign_keys=ON")
            try transaction {
                try execute("CREATE TABLE IF NOT EXISTS projects (id TEXT PRIMARY KEY, name TEXT NOT NULL, goal TEXT NOT NULL, progress INTEGER NOT NULL CHECK(progress BETWEEN 0 AND 100), next_action TEXT NOT NULL, created_at TEXT NOT NULL)")
                try execute("CREATE TABLE IF NOT EXISTS rules (id TEXT PRIMARY KEY, title TEXT NOT NULL, active INTEGER NOT NULL, created_day TEXT NOT NULL)")
                try execute("CREATE TABLE IF NOT EXISTS tasks (id TEXT PRIMARY KEY, title TEXT NOT NULL, day TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0, completed_at TEXT, project_id TEXT REFERENCES projects(id), rule_id TEXT REFERENCES rules(id), action_key TEXT, deleted_at TEXT, created_at TEXT NOT NULL, UNIQUE(day, rule_id), UNIQUE(day, project_id, action_key))")
                try execute("CREATE INDEX IF NOT EXISTS tasks_day ON tasks(day)")
                try execute("PRAGMA user_version=1")
            }
        } catch { sqlite3_close(db); db = nil; throw error }
    }
    deinit { if let db { sqlite3_close(db) } }
    private func query(_ sql: String, _ args: [String?] = []) throws -> [[String: String]] {
        var stmt: OpaquePointer?
        guard sqlite3_prepare_v2(db, sql, -1, &stmt, nil) == SQLITE_OK else { throw failure() }
        defer { sqlite3_finalize(stmt) }
        for (i, arg) in args.enumerated() {
            let code: Int32
            if let arg { code = sqlite3_bind_text(stmt, Int32(i + 1), arg, -1, unsafeBitCast(-1, to: sqlite3_destructor_type.self)) }
            else { code = sqlite3_bind_null(stmt, Int32(i + 1)) }
            guard code == SQLITE_OK else { throw failure() }
        }
        var rows: [[String: String]] = []
        while true {
            let result = sqlite3_step(stmt)
            if result == SQLITE_DONE { return rows }
            guard result == SQLITE_ROW else { throw failure() }
            var row: [String: String] = [:]
            for i in 0..<sqlite3_column_count(stmt) {
                if let value = sqlite3_column_text(stmt, i) { row[String(cString: sqlite3_column_name(stmt, i))] = String(cString: value) }
            }
            rows.append(row)
        }
    }
    private func failure() -> NoteError { NoteError("数据库操作失败：\(String(cString: sqlite3_errmsg(db)))。原文件保留在 \(path)") }
    private func execute(_ sql: String, _ args: [String?] = []) throws { _ = try query(sql, args) }
    private func transaction<T>(_ body: () throws -> T) throws -> T {
        try execute("BEGIN IMMEDIATE")
        do { let result = try body(); try execute("COMMIT"); return result }
        catch { try? execute("ROLLBACK"); throw error }
    }
    private func clean(_ title: String) throws -> String {
        let value = title.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !value.isEmpty else { throw NoteError("名称不能为空。") }
        guard value.count <= 2000 else { throw NoteError("名称请控制在 2000 字以内。") }
        return value
    }
    private func changed() throws { guard sqlite3_changes(db) > 0 else { throw NoteError("记录不存在或已被删除，请刷新后重试。") } }
    private var now: String { ISO8601DateFormatter().string(from: Date()) }
    private func todo(_ r: [String: String]) -> Todo {
        Todo(id: r["id"]!, title: r["title"]!, day: r["day"]!, done: r["done"] == "1", completedAt: r["completed_at"], projectID: r["project_id"], ruleID: r["rule_id"])
    }
    public func tasks(day: String) throws -> [Todo] {
        try Self.validateDay(day)
        return try query("SELECT * FROM tasks WHERE day=? AND deleted_at IS NULL ORDER BY done, CASE WHEN done=1 THEN completed_at END DESC, created_at, rowid", [day]).map(todo)
    }
    public func addTask(title: String, day: String = Store.day()) throws -> String {
        try Self.validateDay(day); let title = try clean(title); let id = UUID().uuidString
        try execute("INSERT INTO tasks(id,title,day,created_at) VALUES(?,?,?,?)", [id,title,day,now]); return id
    }
    public func renameTask(id: String, title: String) throws {
        try execute("UPDATE tasks SET title=? WHERE id=? AND deleted_at IS NULL", [try clean(title),id]); try changed()
    }
    public func setDone(id: String, done: Bool) throws {
        try execute("UPDATE tasks SET done=?,completed_at=CASE WHEN ?='0' THEN NULL ELSE COALESCE(completed_at,?) END WHERE id=? AND deleted_at IS NULL", [done ? "1" : "0",done ? "1" : "0",now,id]); try changed()
    }
    public func deleteTask(id: String) throws {
        try execute("UPDATE tasks SET deleted_at=? WHERE id=? AND deleted_at IS NULL", [now,id]); try changed()
    }
    public func restoreTask(id: String) throws {
        try execute("UPDATE tasks SET deleted_at=NULL WHERE id=? AND deleted_at IS NOT NULL", [id]); try changed()
    }
    public func rules() throws -> [DailyRule] {
        try query("SELECT * FROM rules ORDER BY rowid").map { DailyRule(id:$0["id"]!,title:$0["title"]!,active:$0["active"] == "1") }
    }
    public func addRule(title: String, day: String = Store.day()) throws -> String {
        try Self.validateDay(day); let title = try clean(title); let id = UUID().uuidString
        try transaction {
            try execute("INSERT INTO rules VALUES(?,?,1,?)", [id,title,day])
            try ensureDayInside(day)
        }; return id
    }
    public func updateRule(id: String, title: String? = nil, active: Bool? = nil) throws {
        try transaction {
            guard try query("SELECT id FROM rules WHERE id=?",[id]).first != nil else { throw NoteError("重复事项不存在。") }
            if let title { try execute("UPDATE rules SET title=? WHERE id=?", [try clean(title),id]) }
            if let active { try execute("UPDATE rules SET active=? WHERE id=?", [active ? "1" : "0",id]) }
        }
    }
    public func ensureDay(_ day: String = Store.day()) throws {
        try Self.validateDay(day)
        // No write transaction on the one-second UI refresh unless a rule is missing.
        let missing = try query("SELECT r.id FROM rules r WHERE active=1 AND created_day<=? AND NOT EXISTS(SELECT 1 FROM tasks t WHERE t.rule_id=r.id AND t.day=?) LIMIT 1", [day,day])
        if !missing.isEmpty { try transaction { try ensureDayInside(day) } }
    }
    private func ensureDayInside(_ day: String) throws {
        for rule in try query("SELECT * FROM rules WHERE active=1 AND created_day<=?",[day]) {
            try execute("INSERT INTO tasks(id,title,day,rule_id,created_at) VALUES(?,?,?,?,?) ON CONFLICT(day,rule_id) DO NOTHING", [UUID().uuidString,rule["title"],day,rule["id"],now])
        }
    }
    public func projects() throws -> [Project] {
        try query("SELECT * FROM projects ORDER BY created_at,rowid").map { Project(id:$0["id"]!,name:$0["name"]!,goal:$0["goal"]!,progress:Int($0["progress"]!)!,nextAction:$0["next_action"]!) }
    }
    public func addProject(name: String, goal: String = "", progress: Int = 0, nextAction: String = "") throws -> String {
        guard (0...100).contains(progress) else { throw NoteError("进度必须为 0–100。") }
        let id = UUID().uuidString
        try execute("INSERT INTO projects VALUES(?,?,?,?,?,?)", [id,try clean(name),goal,String(progress),nextAction,now]); return id
    }
    public func updateProject(id: String, name: String? = nil, goal: String? = nil, progress: Int? = nil, nextAction: String? = nil) throws {
        if let progress, !(0...100).contains(progress) { throw NoteError("进度必须为 0–100。") }
        try transaction {
            guard try query("SELECT id FROM projects WHERE id=?",[id]).first != nil else { throw NoteError("项目不存在。") }
            if let name { try execute("UPDATE projects SET name=? WHERE id=?",[try clean(name),id]) }
            if let goal { try execute("UPDATE projects SET goal=? WHERE id=?",[goal,id]) }
            if let progress { try execute("UPDATE projects SET progress=? WHERE id=?",[String(progress),id]) }
            if let nextAction { try execute("UPDATE projects SET next_action=? WHERE id=?",[nextAction,id]) }
        }
    }
    public func addProjectAction(id: String, day: String = Store.day()) throws -> String {
        try Self.validateDay(day)
        return try transaction {
            guard let p = try query("SELECT * FROM projects WHERE id=?",[id]).first else { throw NoteError("项目不存在。") }
            let action = try clean(p["next_action"]!)
            if let old = try query("SELECT id FROM tasks WHERE project_id=? AND day=? AND action_key=?",[id,day,action]).first {
                try execute("UPDATE tasks SET deleted_at=NULL WHERE id=?",[old["id"]]); return old["id"]!
            }
            let taskID = UUID().uuidString
            try execute("INSERT INTO tasks(id,title,day,project_id,action_key,created_at) VALUES(?,?,?,?,?,?)",[taskID,action,day,id,action,now]); return taskID
        }
    }
    public func projectHistory(id: String) throws -> [Todo] {
        try query("SELECT * FROM tasks WHERE project_id=? AND done=1 AND deleted_at IS NULL ORDER BY completed_at DESC LIMIT 20",[id]).map(todo)
    }
}
