@echo off
chcp 65001 >nul
cd /d "%~dp0"
start "" "F:\anaconda3\envs\cosyvoice\python.exe" main.py
