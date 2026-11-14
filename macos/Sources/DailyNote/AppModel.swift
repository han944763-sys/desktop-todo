import AppKit
import SwiftUI
import ServiceManagement
import TaskCore

@MainActor final class AppModel: ObservableObject {
    let store: Store
    @Published var tasks: [Todo] = []
    @Published var projects: [Project] = []
    @Published var rules: [DailyRule] = []
    @Published var recent: [String:[Todo]] = [:]
    @Published var selectedDate = Date()
    @Published var error: String?
    @Published var undoIDs: [String] = []
    @Published var pinned = UserDefaults.standard.bool(forKey:"pinned")
    @Published var loginStatus = SMAppService.mainApp.status
    @Published var reduceTransparency = NSWorkspace.shared.accessibilityDisplayShouldReduceTransparency
    var window: NSWindow?
    private var timer: Timer?
    private var lastDay = Store.day()
    var day: String { Store.day(selectedDate) }
    var isToday: Bool { day == Store.day() }
    init(store: Store) {
        self.store = store
        refresh()
        timer = Timer.scheduledTimer(withTimeInterval:1, repeats:true) { [weak self] _ in
            Task { @MainActor in self?.refresh() }
        }
        NSWorkspace.shared.notificationCenter.addObserver(self,selector:#selector(wake),name:NSWorkspace.didWakeNotification,object:nil)
        NSWorkspace.shared.notificationCenter.addObserver(self,selector:#selector(wake),name:NSWorkspace.accessibilityDisplayOptionsDidChangeNotification,object:nil)
    }
    @objc private func wake() { refresh() }
    func refresh() {
        do {
            let today = Store.day()
            if today != lastDay { if day == lastDay { selectedDate = Date() }; lastDay = today }
            try store.ensureDay(today)
            let t = try store.tasks(day:day); if t != tasks { tasks = t }
            let p = try store.projects(); if p != projects { projects = p }
            let r = try store.rules(); if r != rules { rules = r }
            var history: [String:[Todo]] = [:]
            for project in p { history[project.id] = try store.projectHistory(id:project.id) }
            if history != recent { recent = history }
            let status = SMAppService.mainApp.status; if loginStatus != status { loginStatus = status }
            let reduced = CommandLine.arguments.contains("--reduce-transparency") || NSWorkspace.shared.accessibilityDisplayShouldReduceTransparency
            if reduceTransparency != reduced { reduceTransparency = reduced }
        } catch { if self.error == nil { self.error = error.localizedDescription } }
    }
    @discardableResult func perform(_ action: () throws -> Void) -> Bool {
        do { try action(); refresh(); return true }
        catch { self.error = error.localizedDescription; return false }
    }
    func delete(_ task: Todo) { if perform({ try store.deleteTask(id:task.id) }) { undoIDs.append(task.id) } }
    func undo() { if let id = undoIDs.last, perform({ try store.restoreTask(id:id) }) { undoIDs.removeLast() } }
    func setPinned(_ value: Bool) {
        pinned = value; UserDefaults.standard.set(value,forKey:"pinned")
        window?.level = value ? .floating : .normal
    }
    func setLogin(_ enabled: Bool) {
        perform {
            if enabled { try SMAppService.mainApp.register() }
            else { try SMAppService.mainApp.unregister() }
        }
    }
    func enableLoginOnFirstLaunch() {
        guard !UserDefaults.standard.bool(forKey:"loginConfigured") else { return }
        UserDefaults.standard.set(true,forKey:"loginConfigured")
        if SMAppService.mainApp.status == .notRegistered { setLogin(true) }
    }
}
