#Requires -Version 5.1
# apikey.enc -> %USERPROFILE%\.local\share\opencode\auth.json
# Parola klavyeden alinir, dosyaya/diska ASLA yazilmaz.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$encPath = Join-Path $root "apikey.enc"
if (-not (Test-Path $encPath)) { Write-Host "[coz] apikey.enc yok."; exit 1 }
$sec = Read-Host "Parola" -AsSecureString
$pw = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
  [Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec))
try {
  $blob = [Convert]::FromBase64String(([IO.File]::ReadAllText($encPath)).Trim())
  $obj = [Text.Encoding]::UTF8.GetString($blob) | ConvertFrom-Json
  $salt = [Convert]::FromBase64String($obj.salt)
  $iv = [Convert]::FromBase64String($obj.iv)
  $ct = [Convert]::FromBase64String($obj.ct)
  $kdf = New-Object Security.Cryptography.Rfc2898DeriveBytes($pw, $salt, [int]$obj.iter, [Security.Cryptography.HashAlgorithmName]::SHA256)
  $aes = [Security.Cryptography.Aes]::Create()
  $aes.KeySize = 256; $aes.Mode = "CBC"; $aes.Padding = "PKCS7"
  $aes.Key = $kdf.GetBytes(32); $aes.IV = $iv
  $dec = $aes.CreateDecryptor()
  $plain = $dec.TransformFinalBlock($ct, 0, $ct.Length)
  $aes.Dispose(); $kdf.Dispose()
  $text = [Text.Encoding]::UTF8.GetString($plain)
  $null = $text | ConvertFrom-Json  # bozuksa burada patlar
} finally {
  if ($pw) { $pw = $null }
}
$dst = Join-Path $env:USERPROFILE ".local\share\opencode\auth.json"
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dst) | Out-Null
[IO.File]::WriteAllText($dst, $text, (New-Object Text.UTF8Encoding($false)))
Write-Host "[coz] yazildi: $dst"
