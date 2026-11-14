import Foundation
import TaskCore

final class StoreTests {
    var directory: URL!
    var store: Store!
    func setUpWithError() throws {
        directory = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        store = try Store(path:directory.appendingPathComponent("test.sqlite3").path)
    }
    func tearDownWithError() throws { store = nil; try FileManager.default.removeItem(at:directory) }
    func testCompleteRestoreRenameAndPersistence() throws {
        let id = try store.addTask(title:"  写论文  ",day:"2026-09-20")
        try store.setDone(id:id,done:true)
        try checkTrue(try store.tasks(day:"2026-09-20")[0].done)
        try checkNotNil(try store.tasks(day:"2026-09-20")[0].completedAt)
        try store.renameTask(id:id,title:"修改标题")
        let second = try Store(path:store.path)
        try checkEqual(try second.tasks(day:"2026-09-20")[0].title,"修改标题")
        try second.setDone(id:id,done:false)
        try checkNil(try store.tasks(day:"2026-09-20")[0].completedAt)
        try store.deleteTask(id:id)
        try checkTrue(try store.tasks(day:"2026-09-20").isEmpty)
        try store.restoreTask(id:id)
        try checkEqual(try store.tasks(day:"2026-09-20").count,1)
    }
    func testNoCarryAndNoMissedDayBackfill() throws {
        _ = try store.addTask(title:"昨天未完成",day:"2026-09-20")
        _ = try store.addRule(title:"散步",day:"2026-09-20")
        try store.ensureDay("2026-09-23"); try store.ensureDay("2026-09-23")
        try checkEqual(try store.tasks(day:"2026-09-23").map(\.title),["散步"])
        try checkEqual(try store.tasks(day:"2026-09-20").count,2)
        try checkTrue(try store.tasks(day:"2026-09-21").isEmpty)
        try checkTrue(try store.tasks(day:"2026-09-22").isEmpty)
    }
    func testRuleEditsPauseResumeAndDeletedOccurrence() throws {
        let rule = try store.addRule(title:"阅读",day:"2026-09-20")
        let first = try unwrap(store.tasks(day:"2026-09-20").first)
        try store.setDone(id:first.id,done:true)
        try store.updateRule(id:rule,title:"阅读 20 分钟")
        try store.ensureDay("2026-09-21")
        try checkEqual(try store.tasks(day:"2026-09-20")[0].title,"阅读")
        try checkEqual(try store.tasks(day:"2026-09-21")[0].title,"阅读 20 分钟")
        try checkFalse(try store.tasks(day:"2026-09-21")[0].done)
        try store.updateRule(id:rule,active:false); try store.ensureDay("2026-09-22")
        try checkTrue(try store.tasks(day:"2026-09-22").isEmpty)
        try store.updateRule(id:rule,active:true); try store.ensureDay("2026-09-23")
        let task = try unwrap(store.tasks(day:"2026-09-23").first)
        try store.deleteTask(id:task.id); try store.ensureDay("2026-09-23")
        try checkTrue(try store.tasks(day:"2026-09-23").isEmpty)
    }
    func testProjectActionDedupHistoryAndPartialUpdate() throws {
        let id = try store.addProject(name:"论文",goal:"投稿",progress:20,nextAction:"改图")
        let task = try store.addProjectAction(id:id,day:"2026-09-20")
        try checkEqual(task,try store.addProjectAction(id:id,day:"2026-09-20"))
        try store.setDone(id:task,done:true)
        try checkEqual(try store.projectHistory(id:id).count,1)
        try checkEqual(try store.projects()[0].progress,20)
        let other = try Store(path:store.path)
        try other.updateProject(id:id,progress:55)
        try store.updateProject(id:id,goal:"完成投稿")
        try checkEqual(try store.projects()[0].progress,55)
        try store.setDone(id:task,done:false)
        try checkTrue(try store.projectHistory(id:id).isEmpty)
        try store.deleteTask(id:task)
        try checkEqual(task,try store.addProjectAction(id:id,day:"2026-09-20"))
        try checkEqual(try store.tasks(day:"2026-09-20").count,1)
        try store.updateProject(id:id,nextAction:"改摘要")
        _ = try store.addProjectAction(id:id,day:"2026-09-20")
        try checkEqual(try store.tasks(day:"2026-09-20").count,2)
    }
    func testInvalidInputAndTransactionalRollback() throws {
        checkThrows(try store.addTask(title:"  "))
        checkThrows(try store.addTask(title:"test",day:"2026-02-30"))
        checkThrows(try store.addProject(name:"test",progress:101))
        checkThrows(try store.renameTask(id:"missing",title:"test"))
        let p = try store.addProject(name:"保留")
        checkThrows(try store.updateProject(id:p,name:"  ",goal:"不保存"))
        try checkEqual(try store.projects()[0].name,"保留")
        try checkEqual(try store.projects()[0].goal,"")
    }
    func testCorruptDatabaseIsPreserved() throws {
        let path = directory.appendingPathComponent("corrupt.db")
        let bytes = Data("this is not sqlite data".utf8); try bytes.write(to:path)
        checkThrows(try Store(path:path.path))
        try checkEqual(try Data(contentsOf:path),bytes)
    }
    func testMultipleConnectionsDoNotOverwriteEachOther() throws {
        let second = try Store(path:store.path)
        for n in 0..<30 {
            _ = try store.addTask(title:"GUI \(n)",day:"2026-09-20")
            _ = try second.addTask(title:"CLI \(n)",day:"2026-09-20")
        }
        try checkEqual(try store.tasks(day:"2026-09-20").count,60)
    }
}

// Standalone harness: works with Command Line Tools without the Xcode XCTest SDK.
func checkEqual<T: Equatable>(_ a: @autoclosure () throws -> T, _ b: @autoclosure () throws -> T, file: StaticString = #file, line: UInt = #line) rethrows {
    let lhs = try a(), rhs = try b(); precondition(lhs == rhs, "Expected equal: \(lhs) / \(rhs)", file:file,line:line)
}
func checkTrue(_ value: @autoclosure () throws -> Bool) rethrows { let v = try value(); precondition(v) }
func checkFalse(_ value: @autoclosure () throws -> Bool) rethrows { let v = try value(); precondition(!v) }
func checkNil<T>(_ value: @autoclosure () throws -> T?) rethrows { let v = try value(); precondition(v == nil) }
func checkNotNil<T>(_ value: @autoclosure () throws -> T?) rethrows { let v = try value(); precondition(v != nil) }
func checkThrows<T>(_ body: @autoclosure () throws -> T) { do { _ = try body(); fatalError("Expected an error") } catch {} }
func unwrap<T>(_ value: T?) throws -> T { guard let value else { throw NoteError("Expected a value") }; return value }

@main struct CoreChecks {
    static func main() throws {
        let suite = StoreTests()
        let cases: [(String, () throws -> Void)] = [
            ("complete, undo, persistence",suite.testCompleteRestoreRenameAndPersistence),
            ("no carry or backfill",suite.testNoCarryAndNoMissedDayBackfill),
            ("repeat editing and dedup",suite.testRuleEditsPauseResumeAndDeletedOccurrence),
            ("project history and partial updates",suite.testProjectActionDedupHistoryAndPartialUpdate),
            ("validation and rollback",suite.testInvalidInputAndTransactionalRollback),
            ("corruption preservation",suite.testCorruptDatabaseIsPreserved),
            ("multiple connections",suite.testMultipleConnectionsDoNotOverwriteEachOther)
        ]
        for (name,test) in cases { try suite.setUpWithError(); try test(); try suite.tearDownWithError(); print("PASS: " + name) }
        print("All 7 core checks passed.")
    }
}
