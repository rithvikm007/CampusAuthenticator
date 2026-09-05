@echo off
cd /d "%~dp0"
echo stop > stop.flag
echo Requested graceful shutdown. The script will logout and exit within a second.
