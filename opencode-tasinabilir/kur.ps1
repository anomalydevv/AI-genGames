#Requires -Version 5.1
# Ilk kurulum: opencode-ai'nin guncel surumunu indirip bin\opencode.exe'yi cikarir.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$bin = Join-Path $root "bin"
New-Item -ItemType Directory -Force -Path $bin | Out-Null
$meta = Invoke-RestMethod -Uri "https://registry.npmjs.org/opencode-ai/latest" -TimeoutSec 60
$ver = $meta.version
Write-Host "[kur] surum: $ver"
$tgz = Join-Path $env:TEMP ("opencode-ai-" + $ver + ".tgz")
Invoke-WebRequest -Uri ("https://registry.npmjs.org/opencode-ai/-/opencode-ai-" + $ver + ".tgz") -OutFile $tgz -TimeoutSec 600
$tmp = Join-Path $env:TEMP ("opencode-ai-" + $ver)
if (Test-Path $tmp) { Remove-Item -Recurse -Force $tmp }
New-Item -ItemType Directory -Force -Path $tmp | Out-Null
tar -xzf $tgz -C $tmp
Copy-Item (Join-Path $tmp "package\bin\opencode.exe") (Join-Path $bin "opencode.exe") -Force
Remove-Item -Force $tgz
Remove-Item -Recurse -Force $tmp
Write-Host "[kur] tamam."
