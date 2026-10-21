# BUDDY-Fish-TTS Environment & Hardware Diagnostic Script

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "BUDDY-Fish-TTS -- Environment and Hardware Diagnostics" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

function Report-Check {
    param(
        [string]$Name,
        [bool]$Passed,
        [string]$Details
    )
    if ($Passed) {
        Write-Host " [PASS] $Name : $Details" -ForegroundColor Green
    } else {
        Write-Host " [WARN] $Name : $Details" -ForegroundColor Yellow
    }
}

# 1. Operating System
$os = Get-CimInstance Win32_OperatingSystem
$osDesc = $os.Caption + " (" + $os.OSArchitecture + ", Build " + $os.BuildNumber + ")"
Report-Check -Name "Operating System" -Passed $true -Details $osDesc

# 2. NVIDIA GPU & VRAM
try {
    $smiOut = nvidia-smi --query-gpu=name,driver_version,memory.total,memory.free --format=csv,noheader
    if ($smiOut) {
        $parts = $smiOut.Split(',')
        $gpuName = $parts[0].Trim()
        $driverVer = $parts[1].Trim()
        $vramTotal = $parts[2].Trim()
        $vramFree = $parts[3].Trim()
        Report-Check -Name "NVIDIA GPU" -Passed $true -Details "$gpuName (Driver: $driverVer)"
        Report-Check -Name "Dedicated VRAM" -Passed $true -Details "Total: $vramTotal, Available: $vramFree"
    } else {
        Report-Check -Name "NVIDIA GPU" -Passed $false -Details "nvidia-smi returned no output"
    }
} catch {
    Report-Check -Name "NVIDIA GPU" -Passed $false -Details "nvidia-smi not accessible in PATH"
}

# 3. System RAM
$ramBytes = (Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory
$ramGB = [math]::Round($ramBytes / 1GB, 1)
$ramPass = ($ramGB -ge 14.0)
Report-Check -Name "System RAM" -Passed $ramPass -Details "$ramGB GB Total Physical Memory"

# 4. Free Disk Space
$drive = Get-PSDrive -Name E -ErrorAction SilentlyContinue
if (-not $drive) { $drive = Get-PSDrive -Name C }
$freeGB = [math]::Round($drive.Free / 1GB, 1)
$diskPass = ($freeGB -ge 20)
$driveLetter = $drive.Name
Report-Check -Name "Disk Space ($driveLetter)" -Passed $diskPass -Details "$freeGB GB free space"

# 5. Python Runtime
try {
    $pyVer = python --version
    Report-Check -Name "Python" -Passed $true -Details "$pyVer"
} catch {
    Report-Check -Name "Python" -Passed $false -Details "Python is not in PATH"
}

# 6. MSVC C++ Build Tools
$vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
if (Test-Path $vswhere) {
    $vsPath = & $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
    $hasVs = [bool]$vsPath
    Report-Check -Name "MSVC Build Tools" -Passed $hasVs -Details "$vsPath"
} else {
    Report-Check -Name "MSVC Build Tools" -Passed $false -Details "vswhere.exe not found"
}

# 7. Engine Executable (s2.exe)
$s2Exe = Join-Path $PSScriptRoot "..\s2.cpp\build\Release\s2.exe"
$s2Built = Test-Path $s2Exe
Report-Check -Name "Engine Binary (s2.exe)" -Passed $s2Built -Details "$s2Exe"

# 8. Model File (s2-pro-q5_k_m.gguf)
$modelPath = Join-Path $PSScriptRoot "..\models\s2-pro-q5_k_m.gguf"
if (Test-Path $modelPath) {
    $fileLen = (Get-Item $modelPath).Length
    $modelSize = [math]::Round($fileLen / 1GB, 2)
    $modelDone = ($modelSize -ge 3.5)
    Report-Check -Name "GGUF Model Weights" -Passed $modelDone -Details "$modelPath ($modelSize GB)"
} else {
    Report-Check -Name "GGUF Model Weights" -Passed $false -Details "Not downloaded yet. Run scripts/download_model.py"
}

# 9. Tokenizer
$tokPath = Join-Path $PSScriptRoot "..\models\tokenizer.json"
$tokPass = Test-Path $tokPath
Report-Check -Name "Tokenizer" -Passed $tokPass -Details "$tokPath"

Write-Host "=================================================================" -ForegroundColor Cyan
