// swift-tools-version: 5.9
import PackageDescription
let package = Package(
    name: "DailyNote", platforms: [.macOS(.v13)],
    products: [.executable(name: "DailyNote", targets: ["DailyNote"]), .executable(name: "tasknote", targets: ["TaskCLI"])],
    targets: [
        .systemLibrary(name: "CSQLite"),
        .target(name: "TaskCore", dependencies: ["CSQLite"]),
        .executableTarget(name: "DailyNote", dependencies: ["TaskCore"]),
        .executableTarget(name: "TaskCLI", dependencies: ["TaskCore"]),
        .executableTarget(name: "TaskCoreChecks", dependencies: ["TaskCore"], path: "Tests/TaskCoreTests")
    ])
