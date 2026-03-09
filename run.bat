@echo off
chcp 65001 > nul
echo ============================================================
echo   报纸头版下载与分析工具
echo ============================================================
echo.
echo 正在启动...
echo.

python run.py

if errorlevel 1 (
    echo.
    echo 程序异常退出，按任意键关闭...
    pause > nul
)
