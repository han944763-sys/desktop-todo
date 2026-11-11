$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$chineseName = -join ([char[]](26700, 38754, 28165, 21333))
$executable = (Resolve-Path -LiteralPath (Join-Path $projectRoot "dist\$chineseName.exe")).Path
$tempBase = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
$testRoot = Join-Path $tempBase ('DesktopTodoExeTest-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $testRoot | Out-Null
$previousLocalAppData = $env:LOCALAPPDATA
$processIds = @()

try {
    $env:LOCALAPPDATA = $testRoot
    $first = Start-Process -FilePath $executable -ArgumentList '--autostart' -PassThru -WindowStyle Hidden
    $processIds += $first.Id

    $database = Join-Path $testRoot 'DesktopTodo\todo.db'
    $deadline = [DateTime]::UtcNow.AddSeconds(35)
    while (-not (Test-Path -LiteralPath $database) -and [DateTime]::UtcNow -lt $deadline) {
        Start-Sleep -Milliseconds 500
    }
    $firstAlive = -not $first.HasExited
    $databaseCreated = Test-Path -LiteralPath $database

    $second = Start-Process -FilePath $executable -PassThru -WindowStyle Hidden
    $processIds += $second.Id
    $secondExited = $second.WaitForExit(20000)

    $matching = Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -eq $executable }
    $processIds += @($matching.ProcessId)
    $result = [pscustomobject]@{
        Exe = $executable
        Size = (Get-Item -LiteralPath $executable).Length
        FirstAlive = $firstAlive
        DatabaseCreated = $databaseCreated
        SecondExited = $secondExited
        MatchingProcessCount = @($matching).Count
    }
    $result | Format-List

    if (-not $firstAlive -or -not $databaseCreated -or -not $secondExited) {
        throw 'Packaged executable verification failed.'
    }
}
finally {
    $env:LOCALAPPDATA = $previousLocalAppData
    $processIds | Sort-Object -Unique | ForEach-Object {
        Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
    }
    if (Test-Path -LiteralPath $testRoot) {
        $resolved = (Resolve-Path -LiteralPath $testRoot).Path
        $safePrefix = $tempBase.TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
        $safeLeaf = (Split-Path -Leaf $resolved).StartsWith('DesktopTodoExeTest-')
        if (-not $resolved.StartsWith($safePrefix, [StringComparison]::OrdinalIgnoreCase) -or -not $safeLeaf) {
            throw "Refusing to clean unexpected test path: $resolved"
        }
        Remove-Item -LiteralPath $resolved -Recurse -Force
    }
}
