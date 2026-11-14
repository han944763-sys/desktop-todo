import Foundation
import TaskCore

let help = """
每日任务便签 tasknote — 本地数据接口（JSON 输出）
用法：tasknote [--db 路径] 命令 参数
  list [YYYY-MM-DD]                 查看任务；默认今天
  add 标题 [YYYY-MM-DD]             添加任务
  rename 任务ID 新标题              修改名称
  done 任务ID | undone 任务ID       完成 / 恢复
  delete 任务ID | restore 任务ID    删除 / 撤销删除
  rules                            查看每日重复
  repeat 标题                      新建每日重复（含今天）
  rule-edit ID 标题                 编辑规则（下次生成生效）
  rule-enable ID | rule-disable ID 启用 / 停用规则
  projects                         查看长期项目
  project-add 名称 [目标] [下一步]  新建长期项目
  project-set ID name|goal|progress|next 值
  project-today ID                  下一步加入今日
  project-history ID               最近完成记录
  path                             显示数据库路径
名称或路径有空格时请用引号包裹。ID 请使用列表返回的完整值。
"""
func output<T: Encodable>(_ value: T) throws {
    let encoder = JSONEncoder(); encoder.outputFormatting = [.prettyPrinted,.sortedKeys,.withoutEscapingSlashes]
    print(String(decoding: try encoder.encode(value), as: UTF8.self))
}
do {
    var args = Array(CommandLine.arguments.dropFirst()); var path = Store.defaultPath
    if args.first == "--db" { guard args.count >= 3 else { throw NoteError(help) }; path = args[1]; args.removeFirst(2) }
    let cmd = args.first ?? "help"; args = Array(args.dropFirst())
    if ["help","--help","-h"].contains(cmd) { print(help); exit(0) }
    func count(_ min: Int, _ max: Int? = nil) throws {
        guard args.count >= min && args.count <= (max ?? min) else { throw NoteError("参数数量不正确。\n" + help) }
    }
    let store = try Store(path: path)
    switch cmd {
    case "path": try count(0); print(path)
    case "list":
        try count(0,1); let day = args.first ?? Store.day()
        if day == Store.day() { try store.ensureDay(day) }
        try output(store.tasks(day:day))
    case "add": try count(1,2); try output(["id":store.addTask(title:args[0],day:args.count == 2 ? args[1] : Store.day())])
    case "rename": try count(2); try store.renameTask(id:args[0],title:args[1]); try output(["ok":true])
    case "done", "undone": try count(1); try store.setDone(id:args[0],done:cmd == "done"); try output(["ok":true])
    case "delete": try count(1); try store.deleteTask(id:args[0]); try output(["ok":true])
    case "restore": try count(1); try store.restoreTask(id:args[0]); try output(["ok":true])
    case "rules": try count(0); try output(store.rules())
    case "repeat": try count(1); try output(["id":store.addRule(title:args[0])])
    case "rule-edit": try count(2); try store.updateRule(id:args[0],title:args[1]); try output(["ok":true])
    case "rule-enable", "rule-disable": try count(1); try store.updateRule(id:args[0],active:cmd == "rule-enable"); try store.ensureDay(); try output(["ok":true])
    case "projects": try count(0); try output(store.projects())
    case "project-add": try count(1,3); try output(["id":store.addProject(name:args[0],goal:args.count > 1 ? args[1] : "",nextAction:args.count > 2 ? args[2] : "")])
    case "project-set":
        try count(3)
        switch args[1] {
        case "name": try store.updateProject(id:args[0],name:args[2])
        case "goal": try store.updateProject(id:args[0],goal:args[2])
        case "next": try store.updateProject(id:args[0],nextAction:args[2])
        case "progress": guard let p = Int(args[2]) else { throw NoteError("进度必须为整数。") }; try store.updateProject(id:args[0],progress:p)
        default: throw NoteError("字段应为 name、goal、progress 或 next。")
        }; try output(["ok":true])
    case "project-today": try count(1); try output(["id":store.addProjectAction(id:args[0])])
    case "project-history": try count(1); try output(store.projectHistory(id:args[0]))
    default: throw NoteError("未知命令。\n" + help)
    }
} catch {
    FileHandle.standardError.write(Data((error.localizedDescription + "\n").utf8)); exit(1)
}
