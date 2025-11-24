@echo off
chcp 65001 >nul
cls

echo 🪟 开始构建 Windows 版本 / Starting Windows build...
echo ==================================================

echo 📁 构建目录 / Build directory: %CD%

:: 检查 Python / Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到 Python，请先安装 Python 3.8 或更高版本
    echo ❌ Python not found, please install Python 3.8 or higher
    pause
    exit /b 1
)

:: 创建虚拟环境 / Create virtual environment
echo 📦 创建虚拟环境 / Creating virtual environment...
python -m venv build_venv
call build_venv\Scripts\activate.bat

:: 安装依赖 / Install dependencies
echo 📥 安装依赖 / Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

:: 确保必要的目录存在 / Ensure necessary directories exist
echo 📁 创建必要目录 / Creating necessary directories...
if not exist shots_data mkdir shots_data
if not exist shots_images mkdir shots_images
if not exist plugin mkdir plugin
if not exist assets mkdir assets

:: 构建 / Build
echo 🏗️ 开始构建 / Starting build...
cd ..
cd scripts
pyinstaller print_the_shot.spec
cd ..
cd build

if errorlevel 1 (
    echo ❌ PyInstaller 构建失败 / PyInstaller build failed
    deactivate
    pause
    exit /b 1
)

:: 创建启动批处理文件 / Create startup batch file
echo 📝 创建启动脚本 / Creating startup script...
echo @echo off > dist\start_server.bat
echo chcp 65001 ^>nul >> dist\start_server.bat
echo echo 🍳 PrintTheShot Server 启动中 / Starting... >> dist\start_server.bat
echo cd /d "%%~dp0" >> dist\start_server.bat
echo PrintTheShot_Server.exe >> dist\start_server.bat
echo pause >> dist\start_server.bat

:: 清理 / Cleanup
echo 🧹 清理构建环境 / Cleaning build environment...
deactivate
rmdir /s /q build_venv
rmdir /s /q build

echo.
echo ==================================================
echo ✅ Windows 版本构建完成！/ Windows build completed!
echo 📁 可执行文件位置 / Executable location: dist\PrintTheShot_Server.exe
echo 🚀 启动方式 / Startup methods:
echo    - 双击运行 / Double-click: dist\PrintTheShot_Server.exe
echo    - 使用脚本 / Using script: dist\start_server.bat
echo ==================================================
pause