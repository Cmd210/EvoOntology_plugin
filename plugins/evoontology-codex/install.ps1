$ErrorActionPreference = "Stop"
$pluginRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$skillsRoot = Join-Path $env:USERPROFILE ".agents\skills"
New-Item -ItemType Directory -Path $skillsRoot -Force | Out-Null
Copy-Item -Path (Join-Path $pluginRoot "skills\*") -Destination $skillsRoot -Recurse -Force
Write-Host "Installed EvoOntology skills to $skillsRoot"
