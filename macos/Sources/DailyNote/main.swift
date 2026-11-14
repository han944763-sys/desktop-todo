import AppKit
import SwiftUI
import TaskCore

@MainActor final class AppDelegate: NSObject, NSApplicationDelegate, NSWindowDelegate {
    var window: NSWindow!
    var statusItem: NSStatusItem!
    var model: AppModel!
    func applicationDidFinishLaunching(_ notification: Notification) {
        // Launch Services normally reuses the running instance; also guard direct launches.
        if let bundleID = Bundle.main.bundleIdentifier,
           let other = NSRunningApplication.runningApplications(withBundleIdentifier:bundleID).first(where:{$0.processIdentifier != ProcessInfo.processInfo.processIdentifier}) {
            other.activate(options:[.activateAllWindows]); NSApp.terminate(nil); return
        }
        let arguments = CommandLine.arguments
        if let index = arguments.firstIndex(of:"--appearance"), arguments.count > index + 1 {
            NSApp.appearance = NSAppearance(named:arguments[index + 1] == "dark" ? .darkAqua : .aqua)
        }
        var databasePath = Store.defaultPath
        if let index = arguments.firstIndex(of:"--db"), arguments.count > index + 1 { databasePath = arguments[index + 1] }
        do { model = AppModel(store:try Store(path:databasePath)) }
        catch {
            let alert = NSAlert(); alert.messageText = "无法读取任务数据"; alert.informativeText = error.localizedDescription
            alert.addButton(withTitle:"退出（保留原文件）"); alert.runModal(); NSApp.terminate(nil); return
        }
        let menu = NSMenu()
        menu.addItem(withTitle:"显示每日便签",action:#selector(showWindow),keyEquivalent:"1").target = self
        menu.addItem(withTitle:"置顶 / 取消置顶",action:#selector(togglePin),keyEquivalent:"").target = self
        menu.addItem(.separator())
        menu.addItem(withTitle:"退出每日便签",action:#selector(quit),keyEquivalent:"q").target = self
        statusItem = NSStatusBar.system.statusItem(withLength:NSStatusItem.squareLength)
        statusItem.button?.image = NSImage(systemSymbolName:"checkmark.circle",accessibilityDescription:"每日便签")
        statusItem.button?.toolTip = "每日便签"; statusItem.menu = menu
        let appMenu = NSMenu(); let appItem = NSMenuItem(); appItem.submenu = menu.copy() as? NSMenu; appMenu.addItem(appItem)
        let editItem = NSMenuItem(title:"编辑",action:nil,keyEquivalent:""); let edit = NSMenu(title:"编辑")
        for (name,action,key) in [("撤销",Selector(("undo:")),"z"),("剪切",#selector(NSText.cut(_:)),"x"),("拷贝",#selector(NSText.copy(_:)),"c"),("粘贴",#selector(NSText.paste(_:)),"v"),("全选",#selector(NSText.selectAll(_:)),"a")] {
            edit.addItem(withTitle:name,action:action,keyEquivalent:key)
        }
        editItem.submenu = edit; appMenu.addItem(editItem); NSApp.mainMenu = appMenu
        window = NSWindow(contentRect:NSRect(x:0,y:0,width:300,height:420),styleMask:[.titled,.closable,.miniaturizable,.resizable,.fullSizeContentView],backing:.buffered,defer:false)
        window.title = "每日便签"; window.titleVisibility = .hidden; window.titlebarAppearsTransparent = true
        window.isMovableByWindowBackground = true; window.isReleasedWhenClosed = false; window.delegate = self
        window.minSize = NSSize(width:280,height:300); window.isOpaque = false; window.backgroundColor = .clear
        window.collectionBehavior = [.fullScreenAuxiliary]
        let glass = NSVisualEffectView(); glass.material = .hudWindow; glass.blendingMode = .behindWindow; glass.state = .active
        let host = NSHostingView(rootView:NoteView(model:model).environment(\.locale,Locale(identifier:"zh_CN")))
        host.sizingOptions = [.minSize]
        host.translatesAutoresizingMaskIntoConstraints = false; glass.addSubview(host)
        NSLayoutConstraint.activate([
            host.leadingAnchor.constraint(equalTo:glass.leadingAnchor),host.trailingAnchor.constraint(equalTo:glass.trailingAnchor),
            host.topAnchor.constraint(equalTo:glass.topAnchor,constant:28),host.bottomAnchor.constraint(equalTo:glass.bottomAnchor)
        ])
        window.contentView = glass
        if !window.setFrameUsingName("DailyNoteWindow") {
            if let screen = NSScreen.main { let f = screen.visibleFrame; window.setFrameOrigin(NSPoint(x:f.maxX - 324,y:f.maxY - 448)) }
        }
        // Recover a window saved on a monitor which is no longer connected.
        if !NSScreen.screens.contains(where:{$0.visibleFrame.intersection(window.frame).width >= 100 && $0.visibleFrame.intersection(window.frame).height >= 100}) { window.center() }
        window.setFrameAutosaveName("DailyNoteWindow")
        model.window = window; model.setPinned(model.pinned)
        showWindow()
        if !UserDefaults.standard.bool(forKey:"compactLayoutV2") {
            let old = window.frame
            let size = NSSize(width:min(old.width,300),height:min(old.height,420))
            window.setFrame(NSRect(x:old.maxX-size.width,y:old.maxY-size.height,width:size.width,height:size.height),display:false)
            window.saveFrame(usingName:"DailyNoteWindow")
            UserDefaults.standard.set(true,forKey:"compactLayoutV2")
        }
        if !arguments.contains("--no-login") { model.enableLoginOnFirstLaunch() }
    }
    @objc func showWindow() { model?.refresh(); window?.makeKeyAndOrderFront(nil); NSApp.activate(ignoringOtherApps:true) }
    @objc func togglePin() { model.setPinned(!model.pinned) }
    @objc func quit() { NSApp.terminate(nil) }
    func windowShouldClose(_ sender: NSWindow) -> Bool { sender.orderOut(nil); return false }
    func applicationShouldHandleReopen(_ sender:NSApplication,hasVisibleWindows flag:Bool) -> Bool { showWindow(); return true }
    func applicationShouldTerminateAfterLastWindowClosed(_ sender:NSApplication) -> Bool { false }
}
MainActor.assumeIsolated {
    let app = NSApplication.shared
    let delegate = AppDelegate()
    app.delegate = delegate
    app.setActivationPolicy(.accessory)
    withExtendedLifetime(delegate) { app.run() }
}
