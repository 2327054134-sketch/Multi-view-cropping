@echo off
chcp 65001 > nul
title ViewCrop 重新打包

echo ============================================
echo   ViewCrop 2.0 重新打包 (console=True 调试版)
echo ============================================
echo.

cd /d "%~dp0"

:: 自动找 Python
set PYTHON=
for %%P in (
    "%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python39\python.exe"
    "C:\Python314\python.exe"
    "C:\Python312\python.exe"
    "C:\Python311\python.exe"
    "C:\Python310\python.exe"
) do (
    if exist %%P (
        set PYTHON=%%P
        goto :found_python
    )
)

:: 尝试 conda
for %%C in (
    "%USERPROFILE%\miniconda3\python.exe"
    "%USERPROFILE%\anaconda3\python.exe"
    "%LOCALAPPDATA%\miniconda3\python.exe"
    "%LOCALAPPDATA%\anaconda3\python.exe"
) do (
    if exist %%C (
        set PYTHON=%%C
        goto :found_python
    )
)

echo [ERROR] 找不到 Python！请手动在此脚本里设置 PYTHON 路径。
pause
exit /b 1

:found_python
echo [OK] Python: %PYTHON%
%PYTHON% --version

:: 定位 pyinstaller.exe（和 python.exe 同目录的 Scripts 子目录下）
for %%D in (%PYTHON%) do set PYDIR=%%~dpD
set PYINSTALLER=%PYDIR%Scripts\pyinstaller.exe

if not exist "%PYINSTALLER%" (
    echo [INFO] 正在安装 pyinstaller...
    %PYTHON% -m pip install pyinstaller
)

if not exist "%PYINSTALLER%" (
    echo [ERROR] pyinstaller.exe 仍未找到，请检查安装。
    pause
    exit /b 1
)

echo [OK] PyInstaller: %PYINSTALLER%

echo.
echo [INFO] 清理旧的 dist\ViewCrop_2.0 ...
if exist "dist\ViewCrop_2.0" rmdir /s /q "dist\ViewCrop_2.0"

echo [INFO] 开始打包（使用 ViewCrop_clean.spec）...
echo.
"%PYINSTALLER%" ViewCrop_clean.spec

echo.
if exist "dist\ViewCrop_2.0\ViewCrop_2.0.exe" (
    echo ============================================
    echo   [SUCCESS] 打包成功！
    echo   输出: dist\ViewCrop_2.0\ViewCrop_2.0.exe
    echo ============================================
    echo.
    echo 请双击运行 dist\ViewCrop_2.0\ViewCrop_2.0.exe
    echo 因为 console=True，会有黑色控制台窗口，可以看到报错信息。
) else (
    echo ============================================
    echo   [FAILED] 打包失败，请查看上方错误信息
    echo ============================================
)

pause
