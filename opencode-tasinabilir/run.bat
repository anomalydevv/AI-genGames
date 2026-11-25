@ECHO off
REM Tasinabilir opencode baslatici. Admin gerekmez, internet gerekir (ilk kurulumda).
setlocal
set ROOT=%~dp0
if not exist "%ROOT%bin\opencode.exe" (
  echo [kur] opencode indiriliyor, bekle...
  powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%kur.ps1"
  if errorlevel 1 ( echo [kur] BASARISIZ. & pause & exit /b 1 )
)
REM Kisisel ayarlari kullanici profiline kopyala (yoksa; varsa elleme)
if not exist "%USERPROFILE%\.config\opencode\opencode.json" (
  if not exist "%USERPROFILE%\.config\opencode" mkdir "%USERPROFILE%\.config\opencode"
  copy /Y "%ROOT%opencode.json" "%USERPROFILE%\.config\opencode\opencode.json" >nul
)
if not exist "%USERPROFILE%\.config\opencode\AGENTS.md" copy /Y "%ROOT%AGENTS.md" "%USERPROFILE%\.config\opencode\AGENTS.md" >nul
if not exist "%USERPROFILE%\.config\opencode\skills" xcopy /E /I /Q "%ROOT%skills" "%USERPROFILE%\.config\opencode\skills" >nul
REM ANAHTAR YOKSA: once coz.bat calistir (parola istenir, repoda yazmaz).
"%ROOT%bin\opencode.exe" %*
