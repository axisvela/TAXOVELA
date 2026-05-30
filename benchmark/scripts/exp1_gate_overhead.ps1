param(
    [int]$Repeats = 3,
    [switch]$DryRun,
    [string]$OpenCodeCommand = '& "D:\app\OpenCode\opencode-cli.exe" run --format json --model deepseek/deepseek-v4-flash'
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$ProjectRoot = Resolve-Path (Join-Path $Root "..")
$TasksRoot = Join-Path $Root "tasks"
$Results = Join-Path $Root "results"
New-Item -ItemType Directory -Force -Path $Results | Out-Null

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$OutCsv = Join-Path $Results "exp1_gate_overhead_$Timestamp.csv"
"task_id,task_type,config,run,expected_decision,gate_decision,build_executed,gate_wall_ms,build_wall_ms,total_wall_ms,gate_exit_code,build_exit_code,gate_input_tokens,gate_output_tokens,build_input_tokens,build_output_tokens,final_decision" | Out-File -Encoding utf8 $OutCsv

function Get-ExpectedDecision {
    param([string]$TaskType)
    if ($TaskType -eq "type-a") { return "PASS" }
    if ($TaskType -eq "type-b") { return "BLOCK" }
    if ($TaskType -eq "type-c") { return "REVIEW" }
    return "UNKNOWN"
}

function Get-DecisionFromText {
    param([string]$Text)
    if ($Text -match "\bBLOCK\b") { return "BLOCK" }
    if ($Text -match "\bREVIEW\b") { return "REVIEW" }
    if ($Text -match "\bPASS\b") { return "PASS" }
    return "UNCLEAR"
}

function Get-TokenSum {
    param([string]$Text, [string]$TokenName)
    $sum = 0
    $pattern = '"' + [regex]::Escape($TokenName) + '"\s*:\s*(\d+)'
    foreach ($m in [regex]::Matches($Text, $pattern)) { $sum += [int]$m.Groups[1].Value }
    if ($sum -eq 0 -and $TokenName -eq "input_tokens") {
        foreach ($m in [regex]::Matches($Text, '"input"\s*:\s*(\d+)')) { $sum += [int]$m.Groups[1].Value }
    }
    if ($sum -eq 0 -and $TokenName -eq "output_tokens") {
        foreach ($m in [regex]::Matches($Text, '"output"\s*:\s*(\d+)')) { $sum += [int]$m.Groups[1].Value }
    }
    return $sum
}

function Invoke-OpenCodeRun {
    param(
        [string]$Prompt,
        [string]$ConfigPath,
        [string]$AgentName,
        [string]$SimulatedDecision = "PASS"
    )

    $savedOpenCodeEnv = @{}
    Get-ChildItem Env:OPENCODE* | ForEach-Object {
        $savedOpenCodeEnv[$_.Name] = $_.Value
        Remove-Item "Env:$($_.Name)" -ErrorAction SilentlyContinue
    }
    $env:OPENCODE_CONFIG = $ConfigPath

    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    if ($DryRun) {
        Start-Sleep -Milliseconds (Get-Random -Minimum 100 -Maximum 350)
        $output = "$SimulatedDecision simulated by $AgentName"
        $code = 0
    } else {
        $benchmarkPrompt = @"
BENCHMARK MEASUREMENT ONLY.
Do not modify files, do not run shell commands, and do not call tools.
Evaluate the request according to your assigned agent role and return a concise PASS, BLOCK, or REVIEW decision plus one short reason.

REQUEST:
$Prompt
"@
        $escapedPrompt = $benchmarkPrompt.Replace('"', '`"')
        $agentArg = if ([string]::IsNullOrWhiteSpace($AgentName)) { "" } else { " --agent $AgentName" }
        $cmd = "$OpenCodeCommand$agentArg `"$escapedPrompt`""
        Push-Location $ProjectRoot
        try {
            $output = Invoke-Expression $cmd 2>&1 | Out-String
            $code = $LASTEXITCODE
        } finally {
            Pop-Location
        }
    }
    $sw.Stop()

    Remove-Item Env:OPENCODE_CONFIG -ErrorAction SilentlyContinue
    foreach ($k in $savedOpenCodeEnv.Keys) { Set-Item "Env:$k" $savedOpenCodeEnv[$k] }

    return @{
        WallMs = [int]$sw.ElapsedMilliseconds
        ExitCode = $code
        Decision = Get-DecisionFromText -Text $output
        InputTokens = Get-TokenSum -Text $output -TokenName "input_tokens"
        OutputTokens = Get-TokenSum -Text $output -TokenName "output_tokens"
        Raw = $output
    }
}

$Configs = @(
    @{ Name = "baseline"; Path = Join-Path $Root "configs\opencode-baseline.json" },
    @{ Name = "gate"; Path = Join-Path $Root "configs\opencode-gate.json" }
)

foreach ($config in $Configs) {
    foreach ($taskFile in Get-ChildItem -Path $TasksRoot -Recurse -Filter "*.txt") {
        $taskType = Split-Path (Split-Path $taskFile.FullName -Parent) -Leaf
        $taskId = [System.IO.Path]::GetFileNameWithoutExtension($taskFile.Name)
        $prompt = Get-Content -Raw -Encoding utf8 $taskFile.FullName
        $expected = Get-ExpectedDecision -TaskType $taskType
        for ($run = 1; $run -le $Repeats; $run++) {
            Write-Host "[$($config.Name)] $taskId run $run"
            if ($config.Name -eq "baseline") {
                $build = Invoke-OpenCodeRun -Prompt $prompt -ConfigPath $config.Path -AgentName "build" -SimulatedDecision "PASS"
                $line = "$taskId,$taskType,baseline,$run,$expected,n/a,true,0,$($build.WallMs),$($build.WallMs),0,$($build.ExitCode),0,0,$($build.InputTokens),$($build.OutputTokens),$($build.Decision)"
            } else {
                $gateSim = if ($expected -eq "BLOCK") { "BLOCK" } elseif ($expected -eq "REVIEW") { "REVIEW" } else { "PASS" }
                $gate = Invoke-OpenCodeRun -Prompt $prompt -ConfigPath $config.Path -AgentName "arch-validator" -SimulatedDecision $gateSim
                $buildExecuted = $false
                $buildWall = 0
                $buildExit = 0
                $buildIn = 0
                $buildOut = 0
                $final = $gate.Decision
                if ($gate.Decision -eq "PASS") {
                    $build = Invoke-OpenCodeRun -Prompt $prompt -ConfigPath $config.Path -AgentName "build" -SimulatedDecision "PASS"
                    $buildExecuted = $true
                    $buildWall = $build.WallMs
                    $buildExit = $build.ExitCode
                    $buildIn = $build.InputTokens
                    $buildOut = $build.OutputTokens
                    $final = $build.Decision
                }
                $total = $gate.WallMs + $buildWall
                $line = "$taskId,$taskType,gate,$run,$expected,$($gate.Decision),$buildExecuted,$($gate.WallMs),$buildWall,$total,$($gate.ExitCode),$buildExit,$($gate.InputTokens),$($gate.OutputTokens),$buildIn,$buildOut,$final"
            }
            $line | Out-File -Append -Encoding utf8 $OutCsv
        }
    }
}

Write-Host "[OK] Exp1 results: $OutCsv"
