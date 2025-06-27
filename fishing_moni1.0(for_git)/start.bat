@echo off
title Fishing Game

:: 设置 CMD 编码为 GBK（936）以支持中文
chcp 936 >nul

:: 检查 dist/fishingmoni.exe 是否存在
if not exist "dist\fishingmoni.exe" (
    echo Error: dist\fishingmoni.exe not found! Ensure the executable is in the dist directory.
    pause
    exit /b 1
)

:: 确保 dist 目录存在
if not exist "dist" (
    mkdir dist
)

:: 检查 dist 目录写入权限（使用临时文件）
echo. > dist\temp_test.txt 2>nul
if errorlevel 1 (
    echo Error: Cannot write to dist directory! Ensure the dist directory is writable.
    pause
    exit /b 1
)
del dist\temp_test.txt 2>nul

:: 运行游戏
echo Starting Fishing Game...
dist\fishingmoni.exe

:: 保持窗口打开
echo.
echo Game exited. Press any key to close...
pause >nul