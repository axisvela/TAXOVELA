# ArchHarness installer (PowerShell / Windows)
#   .\install.ps1                # install package + verify
#   .\install.ps1 -SkipInstall   # already installed: just verify
param(
  [switch]$SkipInstall
)
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $Root
try {
  if (-not $SkipInstall) {
    Write-Host 'Installing ArchHarness Python package (editable) ...'
    python -m pip install -e .
    if ($LASTEXITCODE -ne 0) { throw 'pip install failed' }
  }
  if (-not (Test-Path (Join-Path $Root '.archharness\workspace.yaml'))) {
    python -m archharness init-workspace .
    if ($LASTEXITCODE -ne 0) { throw 'workspace init failed' }
  }
  python -m archharness doctor
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

  Write-Host ''
  Write-Host 'Next steps:'
  Write-Host '  1. Edit config.yaml (company name, DC names, platform names).'
  Write-Host '  2. Create a project:  python -m archharness init-project <id> --default'
  Write-Host '  3. Open your AI tool in this directory:'
  Write-Host '       Claude Code : claude .'
  Write-Host '       OpenCode    : opencode .'
  Write-Host '       Codex       : codex (AGENTS.md + .agents/skills auto-discovered)'
  Write-Host '       Copilot/Cursor : open this directory'
  Write-Host '  4. Tools are also reachable anywhere via:'
  Write-Host '       archharness diagram -i arch.yaml'
  Write-Host '       archharness req --doc brief.md'
  Write-Host '       archharness validate-yaml standards/*.yaml config.yaml'
} finally {
  Pop-Location
}
