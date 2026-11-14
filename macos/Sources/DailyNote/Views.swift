import SwiftUI
import AppKit
import ServiceManagement
import TaskCore

private let accent = Color(nsColor:NSColor(name:nil) { appearance in
    if appearance.bestMatch(from:[.aqua,.darkAqua]) == .darkAqua {
        return NSColor(red:0.48,green:0.84,blue:0.71,alpha:1)
    }
    return NSColor(red:0.18,green:0.48,blue:0.40,alpha:1)
})

struct NoteView: View {
    @ObservedObject var model: AppModel
    @State private var title = ""
    @State private var showInput = false
    @State private var showLongTerm = false
    @State private var showHistory = false
    @State private var showRules = false
    @State private var showSettings = false
    @State private var showNewProject = false
    @State private var editingTask: Todo?
    @State private var editingProject: Project?
    @AppStorage("projectsExpanded") private var projectsExpanded = true
    @FocusState private var adding: Bool
    private var todo: [Todo] { model.tasks.filter { !$0.done } }
    private var done: [Todo] { model.tasks.filter(\.done) }
    var body: some View {
        VStack(spacing:0) {
            header
            Divider().opacity(0.45)
            ScrollView {
                VStack(alignment:.leading,spacing:16) {
                    if showLongTerm {
                        projectSection
                    } else {
                        todaySection
                        completedSection
                    }
                }.padding(16)
            }
            footer
        }
        .frame(minWidth:280,minHeight:260)
        .background(model.reduceTransparency ? Color(nsColor:.windowBackgroundColor) : Color.clear)
        .tint(accent)
        .sheet(isPresented:$showRules) { RulesView(model:model) }
        .sheet(isPresented:$showSettings) { SettingsView(model:model) }
        .sheet(isPresented:$showNewProject) { ProjectEditor(model:model,project:nil) }
        .sheet(item:$editingTask) { task in TaskEditor(model:model,task:task) }
        .sheet(item:$editingProject) { project in ProjectEditor(model:model,project:project) }
        .alert("未能完成操作",isPresented:Binding(get:{ model.error != nil },set:{ if !$0 { model.error = nil } })) {
            Button("知道了",role:.cancel) { model.error = nil }
        } message: { Text(model.error ?? "") }
        .onChange(of:model.selectedDate) { _ in model.refresh() }
    }
    private var header: some View {
        VStack(alignment:.leading,spacing:12) {
            HStack {
                Text("每日 · 一点进步").font(.system(size:11,weight:.medium)).foregroundStyle(.secondary)
                Spacer()
                Button { model.setPinned(!model.pinned) } label: { Image(systemName:model.pinned ? "pin.fill" : "pin") }
                    .foregroundStyle(model.pinned ? accent : Color.secondary).help(model.pinned ? "取消置顶" : "置顶便签").accessibilityLabel("切换置顶")
                Button { showLongTerm = false; showHistory.toggle() } label: { Image(systemName:"calendar") }.buttonStyle(.plain).help("按日期查看历史").accessibilityLabel("历史记录")
                    .popover(isPresented:$showHistory) {
                        VStack(alignment:.leading,spacing:12) {
                            Text("查看哪一天？").font(.headline)
                            DatePicker("日期",selection:$model.selectedDate,in:...Date(),displayedComponents:.date).datePickerStyle(.graphical)
                            Button("回到今天") { model.selectedDate = Date(); showHistory = false }
                        }.padding().frame(width:270)
                    }
                Button { showSettings = true } label: { Image(systemName:"gearshape") }.help("设置").accessibilityLabel("设置")
            }.buttonStyle(.plain)
            Picker("任务分类",selection:$showLongTerm) {
                Text("短期 · 今日").tag(false)
                Text("长期目标").tag(true)
            }.pickerStyle(.segmented).labelsHidden().accessibilityLabel("切换短期任务和长期目标")
            if !model.isToday && !showLongTerm {
                HStack { Text("历史 · " + model.day).font(.caption).foregroundStyle(.secondary); Spacer(); Button("今天") { model.selectedDate = Date() }.font(.caption) }
            }
        }.padding(.horizontal,16).padding(.top,6).padding(.bottom,10)
    }
    private var todaySection: some View {
        VStack(alignment:.leading,spacing:12) {
            HStack(spacing:8) {
                sectionTitle(model.isToday ? "今日待办" : "当日待办",count:todo.count,symbol:"sun.max")
                Button {
                    withAnimation(.easeInOut(duration:0.2)) { showInput.toggle() }
                    if !showInput { adding = false }
                } label: {
                    Image(systemName:showInput ? "xmark" : "plus")
                        .font(.system(size:13,weight:.medium)).foregroundStyle(accent)
                        .frame(width:24,height:24).contentShape(Rectangle())
                }.buttonStyle(.plain)
                    .help(showInput ? "收起输入栏" : "添加任务")
                    .accessibilityLabel(showInput ? "收起输入栏" : "展开任务输入栏")
            }
            if showInput {
                HStack(spacing:8) {
                    TextField("写下一个小任务…",text:$title).textFieldStyle(.plain).focused($adding).onSubmit(add)
                        .accessibilityLabel("新任务名称")
                        .task {
                            try? await Task.sleep(nanoseconds:220_000_000)
                            guard !Task.isCancelled else { return }
                            adding = true
                        }
                        .onExitCommand { withAnimation(.easeInOut(duration:0.2)) { showInput = false }; adding = false }
                    Button(action:add) { Image(systemName:"arrow.turn.down.left") }
                        .buttonStyle(.plain).accessibilityLabel("添加任务")
                        .disabled(title.trimmingCharacters(in:.whitespacesAndNewlines).isEmpty)
                }.font(.system(size:13)).padding(11)
                    .background(.primary.opacity(0.045),in:RoundedRectangle(cornerRadius:10))
                    .transition(.move(edge:.top).combined(with:.opacity))
            }
            if todo.isEmpty {
                Text(model.isToday ? (done.isEmpty ? "今天，想从哪件小事开始？" : "清单已打勾，好好享受这一刻。") : "这一天没有未完成任务。")
                    .font(.system(size:12)).foregroundStyle(.secondary).padding(.vertical,6)
            }
            ForEach(todo) { task in taskRow(task) }

        }
    }
    private var completedSection: some View {
        VStack(alignment:.leading,spacing:12) {
            sectionTitle(model.isToday ? "今日已完成" : "当日已完成",count:done.count,symbol:"checkmark.seal")
            if done.isEmpty { Text("每一个勾，都算数。").font(.system(size:12)).foregroundStyle(.tertiary) }
            ForEach(done) { task in taskRow(task) }
        }
    }
    private var projectSection: some View {
        VStack(alignment:.leading,spacing:12) {
            Text("持续推进，选一步加入今日。").font(.system(size:11)).foregroundStyle(.secondary)
            HStack {
                Button { projectsExpanded.toggle() } label: {
                    HStack(spacing:7) { Image(systemName:projectsExpanded ? "chevron.down" : "chevron.right").font(.system(size:9,weight:.bold)); Text("长期目标").font(.system(size:13,weight:.semibold)) }
                }.buttonStyle(.plain)
                Spacer()
                Button { showNewProject = true } label: { Image(systemName:"plus") }.buttonStyle(.plain).help("添加长期目标").accessibilityLabel("添加长期目标")
            }
            if projectsExpanded {
                if model.projects.isEmpty { Text("把大目标，拆成今天的一小步。").font(.system(size:12)).foregroundStyle(.secondary) }
                ForEach(model.projects) { project in
                    VStack(alignment:.leading,spacing:8) {
                        HStack(alignment:.top) {
                            Button { editingProject = project } label: { Text(project.name).font(.system(size:13,weight:.medium)).multilineTextAlignment(.leading) }.buttonStyle(.plain)
                            Spacer(minLength:4)
                            Text("\(project.progress)%").font(.system(size:11,weight:.medium,design:.rounded)).foregroundStyle(accent)
                            Button { editingProject = project } label: { Image(systemName:"ellipsis") }.buttonStyle(.plain).accessibilityLabel("编辑项目 \(project.name)")
                        }
                        ProgressView(value:Double(project.progress),total:100).tint(accent)
                        if !project.goal.isEmpty { Text(project.goal).font(.system(size:11)).foregroundStyle(.secondary).lineLimit(2) }
                        if !project.nextAction.isEmpty {
                            HStack(alignment:.top,spacing:6) {
                                Text("→ " + project.nextAction).font(.system(size:12)).frame(maxWidth:.infinity,alignment:.leading)
                                let added = model.tasks.contains { $0.projectID == project.id && $0.title == project.nextAction } && model.isToday
                                Button(added ? "已加入" : "加入今日") { model.perform { _ = try model.store.addProjectAction(id:project.id) } }
                                    .font(.system(size:10)).buttonStyle(.bordered).disabled(added)
                            }
                        }
                        if let recent = model.recent[project.id]?.first {
                            Text("✓ " + recent.title).font(.system(size:10)).foregroundStyle(.secondary).lineLimit(1)
                        }
                    }.padding(12).background(.primary.opacity(0.035),in:RoundedRectangle(cornerRadius:12))
                }
            }
        }
    }
    private var footer: some View {
        VStack(spacing:0) {
            Divider().opacity(0.45)
            HStack(spacing:8) {
                if !model.undoIDs.isEmpty { Button("撤销删除",action:model.undo).keyboardShortcut("z",modifiers:.command) }
                else if showLongTerm { Text("\(model.projects.count) 个长期目标").foregroundStyle(.secondary) }
                else { Image(systemName:"checkmark.circle.fill").foregroundStyle(accent); Text("已完成 \(done.count) 件").foregroundStyle(.secondary) }
                Spacer(minLength:0)
                Button("每日重复") { showRules = true }.foregroundStyle(.secondary)
            }.font(.system(size:11)).buttonStyle(.plain).padding(.horizontal,16).padding(.vertical,10)
        }
    }
    private func sectionTitle(_ text: String,count: Int,symbol: String) -> some View {
        HStack(spacing:7) {
            Image(systemName:symbol).foregroundStyle(accent)
            Text(text).fontWeight(.semibold)
            Text("\(count)").font(.system(size:10,weight:.medium)).foregroundStyle(.secondary)
                .padding(.horizontal,6).padding(.vertical,2).background(.primary.opacity(0.06),in:Capsule())
            Spacer()
        }.font(.system(size:13))
    }
    private func taskRow(_ task: Todo) -> some View {
        HStack(alignment:.top,spacing:9) {
            Button { model.perform { try model.store.setDone(id:task.id,done:!task.done) } } label: {
                Image(systemName:task.done ? "checkmark.circle.fill" : "circle").font(.system(size:18)).foregroundStyle(task.done ? accent : Color.secondary.opacity(0.6))
            }.buttonStyle(.plain).accessibilityLabel(task.done ? "恢复任务 \(task.title)" : "完成任务 \(task.title)")
            VStack(alignment:.leading,spacing:3) {
                Text(task.title).font(.system(size:13)).strikethrough(task.done).foregroundStyle(task.done ? .secondary : .primary)
                    .fixedSize(horizontal:false,vertical:true).frame(maxWidth:.infinity,alignment:.leading)
                    .onTapGesture(count:2) { editingTask = task }
                if task.ruleID != nil { Text("每日重复").font(.system(size:9)).foregroundStyle(.tertiary) }
                else if let id = task.projectID, let p = model.projects.first(where:{$0.id == id}) { Text(p.name).font(.system(size:9)).foregroundStyle(.tertiary) }
            }
            Menu {
                Button("编辑") { editingTask = task }
                Button("删除",role:.destructive) { model.delete(task) }
            } label: { Image(systemName:"ellipsis").font(.system(size:12)).foregroundStyle(.secondary) }
                .menuStyle(.borderlessButton).menuIndicator(.hidden).fixedSize().accessibilityLabel("任务操作 \(task.title)")
        }.padding(.vertical,3)
    }
    private func add() {
        guard !title.trimmingCharacters(in:.whitespacesAndNewlines).isEmpty else { return }
        if model.perform({ _ = try model.store.addTask(title:title,day:model.day) }) {
            title = ""; adding = false
            withAnimation(.easeInOut(duration:0.2)) { showInput = false }
        }
    }
}

struct TaskEditor: View {
    @ObservedObject var model: AppModel
    let task: Todo
    @Environment(\.dismiss) private var dismiss
    @State private var title: String
    init(model:AppModel,task:Todo) { self.model=model; self.task=task; _title=State(initialValue:task.title) }
    var body: some View {
        VStack(alignment:.leading,spacing:16) {
            Text("编辑任务").font(.headline)
            TextField("任务名称",text:$title,axis:.vertical).lineLimit(2...6).textFieldStyle(.roundedBorder)
            Text("只修改这条任务，不改变每日重复规则。").font(.caption).foregroundStyle(.secondary)
            HStack { Button("取消") { dismiss() }.keyboardShortcut(.cancelAction); Spacer(); Button("保存") {
                if model.perform({ try model.store.renameTask(id:task.id,title:title) }) { dismiss() }
            }.keyboardShortcut(.defaultAction) }
        }.padding(20).frame(width:290)
    }
}
struct ProjectEditor: View {
    @ObservedObject var model: AppModel
    let project: Project?
    @Environment(\.dismiss) private var dismiss
    @State private var name: String
    @State private var goal: String
    @State private var progress: Double
    @State private var next: String
    init(model:AppModel,project:Project?) {
        self.model=model; self.project=project
        _name=State(initialValue:project?.name ?? ""); _goal=State(initialValue:project?.goal ?? "")
        _progress=State(initialValue:Double(project?.progress ?? 0)); _next=State(initialValue:project?.nextAction ?? "")
    }
    var body: some View {
        VStack(alignment:.leading,spacing:14) {
            Text(project == nil ? "新的长期目标" : "编辑长期目标").font(.headline)
            field("项目名称",text:$name)
            field("想达到的目标",text:$goal)
            HStack { Text("当前进度"); Spacer(); Text("\(Int(progress))%") }.font(.caption)
            Slider(value:$progress,in:0...100,step:1)
            field("下一步具体做什么",text:$next)
            if let project, let recent = model.recent[project.id], !recent.isEmpty {
                Text("最近完成").font(.caption).foregroundStyle(.secondary)
                ScrollView { VStack(alignment:.leading,spacing:6) { ForEach(recent) { task in Text("✓ \(task.title) · \(task.day)").font(.caption).frame(maxWidth:.infinity,alignment:.leading) } } }.frame(maxHeight:100)
            }
            HStack {
                Button("取消") { dismiss() }.keyboardShortcut(.cancelAction); Spacer()
                Button("保存") {
                    if model.perform({
                        if let project {
                            // Only write fields this editor changed; preserve concurrent CLI edits to other fields.
                            try model.store.updateProject(id:project.id,name:name == project.name ? nil : name,goal:goal == project.goal ? nil : goal,progress:Int(progress) == project.progress ? nil : Int(progress),nextAction:next == project.nextAction ? nil : next)
                        } else { _ = try model.store.addProject(name:name,goal:goal,progress:Int(progress),nextAction:next) }
                    }) { dismiss() }
                }.keyboardShortcut(.defaultAction)
            }
        }.padding(20).frame(width:290).tint(accent)
    }
    private func field(_ label: String,text: Binding<String>) -> some View {
        VStack(alignment:.leading,spacing:5) { Text(label).font(.caption).foregroundStyle(.secondary); TextField(label,text:text,axis:.vertical).lineLimit(1...4).textFieldStyle(.roundedBorder) }
    }
}
struct RulesView: View {
    @ObservedObject var model: AppModel
    @Environment(\.dismiss) private var dismiss
    @State private var newTitle = ""
    var body: some View {
        VStack(alignment:.leading,spacing:14) {
            Text("每日重复").font(.headline)
            Text("每天一份新的开始，不累积欠账。修改名称次日生效；停用后不再生成，已经生成的任务保留。").font(.caption).foregroundStyle(.secondary)
            ScrollView {
                VStack(spacing:12) {
                    ForEach(model.rules) { rule in RuleRow(model:model,rule:rule) }
                    if model.rules.isEmpty { Text("例如：阅读 20 分钟、散步。 ").font(.caption).foregroundStyle(.secondary).padding() }
                }
            }.frame(maxHeight:260)
            HStack {
                TextField("每天要做的事",text:$newTitle).textFieldStyle(.roundedBorder).onSubmit(add)
                Button("添加",action:add).disabled(newTitle.trimmingCharacters(in:.whitespacesAndNewlines).isEmpty)
            }
            HStack { Spacer(); Button("完成") { dismiss() }.keyboardShortcut(.cancelAction) }
        }.padding(20).frame(width:290).tint(accent)
    }
    private func add() { if model.perform({ _ = try model.store.addRule(title:newTitle) }) { newTitle = "" } }
}
struct RuleRow: View {
    @ObservedObject var model: AppModel
    let rule: DailyRule
    @State private var text: String
    init(model:AppModel,rule:DailyRule) { self.model=model; self.rule=rule; _text=State(initialValue:rule.title) }
    var body: some View {
        VStack(alignment:.leading,spacing:6) {
            HStack {
                TextField("重复事项",text:$text).textFieldStyle(.roundedBorder)
                Button("保存") { model.perform { try model.store.updateRule(id:rule.id,title:text) } }.disabled(text == rule.title)
            }
            Toggle("启用",isOn:Binding(get:{rule.active},set:{ value in model.perform { try model.store.updateRule(id:rule.id,active:value) } })).toggleStyle(.switch).font(.caption)
        }
    }
}
struct SettingsView: View {
    @ObservedObject var model: AppModel
    @Environment(\.dismiss) private var dismiss
    var body: some View {
        VStack(alignment:.leading,spacing:16) {
            Text("便签设置").font(.headline)
            Toggle("始终置顶",isOn:Binding(get:{model.pinned},set:model.setPinned))
            Toggle("登录 Mac 后自动启动",isOn:Binding(get:{model.loginStatus == .enabled || model.loginStatus == .requiresApproval},set:model.setLogin))
            if model.loginStatus == .requiresApproval {
                Text("自启动需要在系统设置中允许。").font(.caption)
                Button("打开登录项设置") { SMAppService.openSystemSettingsLoginItems() }
            }
            Text("原生毛玻璃跟随系统外观。关闭窗口后，点击菜单栏的勾选图标可重新打开。").font(.caption).foregroundStyle(.secondary)
            Button("在 Finder 中查看数据") { NSWorkspace.shared.activateFileViewerSelecting([URL(fileURLWithPath:model.store.path)]) }
            HStack { Spacer(); Button("完成") { dismiss() }.keyboardShortcut(.cancelAction) }
        }.padding(20).frame(width:290).toggleStyle(.switch).tint(accent)
    }
}
