# Standardized Reception Test Script for BUDDY-Fish-TTS

param(
    [switch]$PlayAudio = $false
)

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "BUDDY-Fish-TTS -- Reception Voice Synthesis Benchmark" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

$baseDir = Resolve-Path (Join-Path $PSScriptRoot "..")
$pythonExe = Join-Path $baseDir "..\.venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$testScript = @"
import sys
import time
from pathlib import Path

# Add app to sys.path
base_dir = Path(r'$baseDir')
sys.path.insert(0, str(base_dir))

from app.tts_engine import FishTTSEngine
from app.config import tts_config

prompt = "Hello! Welcome to Anantrao Pawar College of Engineering and Research. I am Buddy, your AI college receptionist. How can I help you today?"
output_path = str(base_dir / "output" / "buddy_test.wav")

print("Synthesizing test sentence:")
print(f"\"{prompt}\"\n")

engine = FishTTSEngine()
status = engine.get_status()

print("Engine Status:")
print(f"  * Model file:     {Path(tts_config.MODEL_PATH).name}")
print(f"  * Model path:     {tts_config.MODEL_PATH}")
print(f"  * Tokenizer:      {Path(tts_config.TOKENIZER_PATH).name}")
print(f"  * Engine binary:  {Path(tts_config.S2_BINARY_PATH).name}")

if not status["ready"]:
    print("\n[!] Pre-requisites check:")
    for issue in status["issues"]:
        print(f"    - {issue}")
    sys.exit(1)

print("\nStarting synthesis...")
start_time = time.time()
res = engine.generate(text=prompt, output_path=output_path)
total_time = time.time() - start_time

print("\n" + "=" * 65)
print("SYNTHESIS RESULTS & BENCHMARKS")
print("=" * 65)
print(f"  * Output file path:       {res['output_path']}")
print(f"  * Output size:            {res['file_size_bytes'] / 1024:.1f} KB")
print(f"  * Audio duration:         {res['duration_seconds']} seconds")
print(f"  * Generation time:        {res['generation_time_seconds']} seconds")
print(f"  * Real-Time Factor (RTF): {res['real_time_factor']}x")
print(f"  * GPU Memory Allocated:   {res['gpu_memory_used_mb']} MB")
print(f"  * Sample Rate:            {res['sample_rate']} Hz")
print("=" * 65)
"@

$tempPy = Join-Path $env:TEMP "run_buddy_tts_test.py"
Set-Content -Path $tempPy -Value $testScript -Encoding UTF8

& $pythonExe $tempPy
$exitCode = $LASTEXITCODE

Remove-Item -Force $tempPy -ErrorAction SilentlyContinue

if ($exitCode -eq 0 -and $PlayAudio) {
    $outWav = Join-Path $baseDir "output\buddy_test.wav"
    if (Test-Path $outWav) {
        Write-Host "Playing generated audio..." -ForegroundColor Yellow
        $player = New-Object System.Media.SoundPlayer($outWav)
        $player.PlaySync()
    }
}

exit $exitCode
