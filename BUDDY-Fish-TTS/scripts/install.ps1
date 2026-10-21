# BUDDY-Fish-TTS Automated Installer & Builder Script

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "🛠️ BUDDY-Fish-TTS — Installer & Build Setup" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

$baseDir = Resolve-Path (Join-Path $PSScriptRoot "..")
$s2Dir = Join-Path $baseDir "s2.cpp"
$cmakePath = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe"
$vsDevShell = "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\Launch-VsDevShell.ps1"

# 1. Activate Visual Studio Environment
if (Test-Path $vsDevShell) {
    Write-Host "Activating Visual Studio 2022 Build Tools environment..." -ForegroundColor Yellow
    & $vsDevShell -Arch amd64
} else {
    Write-Host "Warning: Visual Studio Build Tools shell script not found at expected path." -ForegroundColor Red
}

# 2. Build s2.cpp
Write-Host "Building s2.cpp engine..." -ForegroundColor Yellow
$buildDir = Join-Path $s2Dir "build"
& $cmakePath -B $buildDir -S $s2Dir -G "Visual Studio 17 2022" -A x64 -DCMAKE_BUILD_TYPE=Release
& $cmakePath --build $buildDir --config Release --parallel

# 3. Copy runtime DLLs next to executable
$releaseDir = Join-Path $buildDir "Release"
$binReleaseDir = Join-Path $buildDir "bin\Release"
if (Test-Path $binReleaseDir) {
    Write-Host "Copying runtime DLLs to $releaseDir ..." -ForegroundColor Yellow
    Copy-Item -Force "$binReleaseDir\*.dll" $releaseDir
}

# 4. Copy tokenizer
$tokSource = Join-Path $s2Dir "tokenizer.json"
$tokTarget = Join-Path $baseDir "models\tokenizer.json"
if (Test-Path $tokSource) {
    Copy-Item -Force $tokSource $tokTarget
    Write-Host "Tokenizer initialized: $tokTarget" -ForegroundColor Green
}

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "✅ s2.cpp build and setup completed successfully!" -ForegroundColor Green
Write-Host "Next step: Run 'python scripts/download_model.py' to fetch GGUF weights."
Write-Host "=================================================================" -ForegroundColor Cyan
