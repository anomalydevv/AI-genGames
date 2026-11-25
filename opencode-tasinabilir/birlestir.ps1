#Requires -Version 5.1
# static/*.part* -> bin\opencode.exe (kopyala-BIRLESTIR, hash dogrulamali). Admin gerekmez.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$bin = Join-Path $root "bin"
New-Item -ItemType Directory -Force -Path $bin | Out-Null
$out = Join-Path $bin "opencode.exe"
$fs = New-Object IO.FileStream($out, [IO.FileMode]::Create)
Get-ChildItem (Join-Path $root "static\opencode.exe.part*") | Sort-Object Name | ForEach-Object {
  $b = [IO.File]::ReadAllBytes($_.FullName)
  $fs.Write($b, 0, $b.Length)
}
$fs.Close()
$h = (Get-FileHash $out -Algorithm SHA256).Hash
if ($h -ne "9A735720499BFAED8FC62DB6F45123AEBFF929F33AF885038068E8068DA51CF5") {
  Remove-Item -Force $out
  Write-Host "[birlestir] HASH UYUSMADI, silindi."
  exit 1
}
Write-Host "[birlestir] tamam."
