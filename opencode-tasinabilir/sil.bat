@ECHO off
REM API anahtarini siler: portable ev (.home) + kullanici profili.
REM EXE'ye, ayarlara ve sifreli dosyaya DOKUNMAZ. Sadece auth.json gider.
del /F /Q "%~dp0.home\.local\share\opencode\auth.json" 2>nul
del /F /Q "%USERPROFILE%\.local\share\opencode\auth.json" 2>nul
echo [sil] anahtarlar silindi.
pause
