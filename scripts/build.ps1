param([string]$OutputName = '')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot

uv sync --locked
uv run python scripts\generate_icon.py

# Nuitka's Windows DLL scanner cannot reliably process non-ASCII build paths.
# Compile from a short-lived ASCII staging directory, then copy only the EXE back.
$tempBase = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
$stageName = 'DesktopTodoBuild-' + [guid]::NewGuid().ToString('N')
$stageRoot = Join-Path $tempBase $stageName
New-Item -ItemType Directory -Path $stageRoot | Out-Null
try {
    Copy-Item -LiteralPath (Join-Path $projectRoot '.python-version') -Destination $stageRoot
    Copy-Item -LiteralPath (Join-Path $projectRoot 'main.py') -Destination $stageRoot
    Copy-Item -LiteralPath (Join-Path $projectRoot 'pyproject.toml') -Destination $stageRoot
    Copy-Item -LiteralPath (Join-Path $projectRoot 'pysidedeploy.spec') -Destination $stageRoot
    Copy-Item -LiteralPath (Join-Path $projectRoot 'README.md') -Destination $stageRoot
    Copy-Item -LiteralPath (Join-Path $projectRoot 'uv.lock') -Destination $stageRoot
    Copy-Item -LiteralPath (Join-Path $projectRoot 'src') -Destination $stageRoot -Recurse

    Push-Location -LiteralPath $stageRoot
    try {
        uv sync --locked
        $nuitkaCompilerRoot = Join-Path $env:LOCALAPPDATA 'Nuitka\Nuitka\Cache\downloads\gcc'
        $nuitkaCc1 = Get-ChildItem -LiteralPath $nuitkaCompilerRoot -Filter 'cc1.exe' -File -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
        $hasMsvc = $null -ne (Get-Command cl.exe -ErrorAction SilentlyContinue)
        if ($hasMsvc -or $nuitkaCc1) {
            try {
                uv run pyside6-deploy -c pysidedeploy.spec --force
            }
            catch {
                Write-Warning 'pyside6-deploy failed; falling back to PyInstaller.'
            }
        }
        else {
            Write-Warning 'No complete Nuitka compiler was found; using PyInstaller.'
        }

        $stagedExecutable = Join-Path $stageRoot 'dist\DesktopTodo.exe'
        if (-not (Test-Path -LiteralPath $stagedExecutable)) {
            $assetSource = Join-Path $stageRoot 'src\desktop_todo\assets'
            $iconSource = Join-Path $assetSource 'icon.ico'
            $dataArgument = "$assetSource;desktop_todo\assets"
            $originalPath = $env:PATH
            try {
                # Do not let PyInstaller collect unrelated ICU DLLs from tool-only PATH entries.
                $env:PATH = (($originalPath -split ';') | Where-Object { $_ -notmatch '\\poppler\\' }) -join ';'
                uv run pyinstaller --noconfirm --clean --onefile --windowed --name DesktopTodo --icon $iconSource --add-data $dataArgument --distpath dist --workpath build\pyinstaller --specpath build\pyinstaller main.py
            }
            finally {
                $env:PATH = $originalPath
            }
        }
    }
    finally {
        Pop-Location
    }

    $builtExecutable = Join-Path $stageRoot 'dist\DesktopTodo.exe'
    if (-not (Test-Path -LiteralPath $builtExecutable)) {
        throw 'The build completed without producing an EXE.'
    }

    $distDirectory = Join-Path $projectRoot 'dist'
    New-Item -ItemType Directory -Path $distDirectory -Force | Out-Null
    $chineseName = -join ([char[]](26700, 38754, 28165, 21333))
    if ($OutputName) {
        if ([IO.Path]::GetFileName($OutputName) -ne $OutputName -or -not $OutputName.EndsWith('.exe')) {
            throw 'OutputName must be an EXE filename, not a path.'
        }
        $target = Join-Path $distDirectory $OutputName
    }
    else {
        $target = Join-Path $distDirectory ("$chineseName.exe")
    }
    Copy-Item -LiteralPath $builtExecutable -Destination $target -Force
    Write-Host "Built: $target"
}
finally {
    if (Test-Path -LiteralPath $stageRoot) {
        $resolvedStage = (Resolve-Path -LiteralPath $stageRoot).Path
        $safePrefix = $tempBase.TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
        if (-not $resolvedStage.StartsWith($safePrefix, [StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing to clean unexpected path: $resolvedStage"
        }
        if (-not (Split-Path -Leaf $resolvedStage).StartsWith('DesktopTodoBuild-')) {
            throw "Refusing to clean unexpected directory: $resolvedStage"
        }
        Remove-Item -LiteralPath $resolvedStage -Recurse -Force
    }
}
