$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$BaseDir = $PSScriptRoot
$Version = "v1.1.2"
$DistName = "dekisugiwin-$Version"
$DistDir = Join-Path $BaseDir "dist"
$DistPath = Join-Path $DistDir $DistName
$ZipPath = Join-Path $DistDir "$DistName.zip"

Write-Host "Creating release directory at: $DistPath" -ForegroundColor Cyan
if (-not (Test-Path $DistDir)) { $null = New-Item -ItemType Directory -Path $DistDir }
if (Test-Path $DistPath) { Remove-Item -Path $DistPath -Recurse -Force }
if (Test-Path $ZipPath) { Remove-Item -Path $ZipPath -Force }
$null = New-Item -ItemType Directory -Path $DistPath -Force

Write-Host "Copying dekisugiwin.exe..." -ForegroundColor Cyan
Copy-Item -Path (Join-Path $BaseDir "dekisugiwin.exe") -Destination $DistPath

Write-Host "Copying bin, config, scripts folders..." -ForegroundColor Cyan
Copy-Item -Path (Join-Path $BaseDir "bin") -Destination $DistPath -Recurse
Copy-Item -Path (Join-Path $BaseDir "config") -Destination $DistPath -Recurse


Write-Host "Cleaning up source files in release package..." -ForegroundColor Cyan
# Ensure no source code accidentally leaks in the release
Get-ChildItem -Path $DistPath -Include "*.ps1", "*.cs", "*.py", "*.md" -Recurse | Remove-Item -Force -ErrorAction SilentlyContinue

Write-Host "Compressing to ZIP..." -ForegroundColor Cyan
Compress-Archive -Path "$DistPath\*" -DestinationPath $ZipPath -Force

Write-Host "Done! Release created at $ZipPath" -ForegroundColor Green
