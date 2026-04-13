$ErrorActionPreference = "Stop"

$workspace = "C:\Users\steph\projects\rowboat-workspace"
$linkPath = "C:\Users\steph\.rowboat"
$installerScript = Join-Path $workspace "scripts\install-rowboat-zaphod.ps1"

if (-not (Test-Path $workspace)) {
  throw "Workspace not found at $workspace"
}

if (-not (Test-Path $installerScript)) {
  throw "Workspace installer script not found at $installerScript"
}

if (-not (Test-Path $linkPath)) {
  cmd /c mklink /J "$linkPath" "$workspace" | Out-Null
}

& $installerScript
