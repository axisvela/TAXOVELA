param(
    [int]$Repeats = 3,
    [int]$Runs = 5,
    [switch]$SkipExp1,
    [switch]$SkipExp2,
    [switch]$DryRun,
    [string]$OpenCodeCommand = '& "D:\app\OpenCode\opencode-cli.exe" run --format json --model deepseek/deepseek-v4-flash'
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Results = Join-Path $Root "results"
New-Item -ItemType Directory -Force -Path $Results | Out-Null

Write-Host "EA-Harness benchmark runner"
Write-Host "Root: $Root"
Write-Host "Results: $Results"

if (-not $SkipExp1) {
    Write-Host "`n[EXP1] Strict gate-to-build overhead"
    & (Join-Path $PSScriptRoot "exp1_gate_overhead.ps1") -Repeats $Repeats -DryRun:$DryRun -OpenCodeCommand $OpenCodeCommand
}

if (-not $SkipExp2) {
    Write-Host "`n[EXP2] Temperature consistency"
    $dry = if ($DryRun) { "--dry-run" } else { "" }
    python (Join-Path $PSScriptRoot "exp2_temperature.py") --runs $Runs $dry
}

Write-Host "`n[ANALYZE] Summaries"
python (Join-Path $PSScriptRoot "analyze_results.py") --results-dir $Results
