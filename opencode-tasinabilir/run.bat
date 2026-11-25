@ECHO off
REM Tasinabilir opencode. Admin gerekmez, hersey bu klasorde (.home).
REM Internet YOKSA: static\ parcalardan exe birlesir. Varsa ve exe yoksa indirilir.
setlocal
set ROOT=%~dp0
set EXE=%ROOT%bin\opencode.exe
if not exist "%EXE%" (
  if exist "%ROOT%static\opencode.exe.part001" (
    echo [kur] parcalar birlestiriliyor, bekle...
    powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%birlestir.ps1"
    if errorlevel 1 ( echo [kur] BASARISIZ. & pause & exit /b 1 )
  ) else (
    echo [kur] indiriliyor, bekle...
    powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%kur.ps1"
    if errorlevel 1 ( echo [kur] BASARISIZ. & pause & exit /b 1 )
  )
)
REM Portable ev: config+data bu klasore yazilir, sisteme dokunulmaz.
set HOME_DIR=%ROOT%.home
if not exist "%HOME_DIR%" mkdir "%HOME_DIR%"
set HOME=%HOME_DIR%
set USERPROFILE=%HOME_DIR%
set XDG_CONFIG_HOME=%HOME_DIR%\.config
set XDG_DATA_HOME=%HOME_DIR%\.local\share
set XDG_CACHE_HOME=%HOME_DIR%\.cache
set LOCALAPPDATA=%HOME_DIR%\AppDataLocal
if not exist "%XDG_CONFIG_HOME%\opencode" mkdir "%XDG_CONFIG_HOME%\opencode"
if not exist "%XDG_CONFIG_HOME%\opencode\opencode.json" copy /Y "%ROOT%opencode.json" "%XDG_CONFIG_HOME%\opencode\opencode.json" >nul
if not exist "%XDG_CONFIG_HOME%\opencode\AGENTS.md" copy /Y "%ROOT%AGENTS.md" "%XDG_CONFIG_HOME%\opencode\AGENTS.md" >nul
if not exist "%XDG_CONFIG_HOME%\opencode\skills" xcopy /E /I /Q "%ROOT%skills" "%XDG_CONFIG_HOME%\opencode\skills" >nul
REM ANAHTAR YOKSA: once coz.bat calistir (parola istenir, repoda yazmaz).
"%EXE%" %*
