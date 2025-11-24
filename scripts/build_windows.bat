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

:: 安装Windows专用依赖 / Install Windows-specific dependencies
echo 📥 安装Windows依赖 / Installing Windows dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

:: 构建 / Build
echo 🏗️ 开始构建 / Starting build...
cd ..
pyinstaller scripts/print_the_shot.spec
cd scripts

if errorlevel 1 (
    echo ❌ PyInstaller 构建失败 / PyInstaller build failed
    deactivate
    pause
    exit /b 1
)

:: 创建启动批处理文件 / Create startup batch file
cd ..
echo 📝 创建启动脚本 / Creating startup script...
echo @echo off > dist\start_server.bat
echo chcp 65001 ^>nul >> dist\start_server.bat
echo echo 🍳 PrintTheShot Server 启动中 / Starting... >> dist\start_server.bat
echo cd /d "%%~dp0" >> dist\start_server.bat
echo PrintTheShot.exe >> dist\start_server.bat
echo pause >> dist\start_server.bat

:: 创建Windows专用的说明文件 / Create Windows-specific readme
echo 📄 创建Windows说明文件 / Creating Windows readme...
echo # PrintTheShot Server - Windows 版本 > dist\README_Windows.txt
echo. >> dist\README_Windows.txt
echo ## 系统要求 / System Requirements >> dist\README_Windows.txt
echo - Windows 10 或更高版本 / Windows 10 or higher >> dist\README_Windows.txt
echo - Python 3.8+ (已包含在可执行文件中) / Python 3.8+ (included in executable) >> dist\README_Windows.txt
echo - 默认打印机已设置 / Default printer configured >> dist\README_Windows.txt
echo. >> dist\README_Windows.txt
echo ## 启动方式 / Startup Methods >> dist\README_Windows.txt
echo 1. 双击 start_server.bat (推荐) / Double-click start_server.bat (recommended) >> dist\README_Windows.txt
echo 2. 双击 PrintTheShot.exe / Double-click PrintTheShot.exe >> dist\README_Windows.txt
echo. >> dist\README_Windows.txt
echo ## 打印支持 / Printing Support >> dist\README_Windows.txt
echo - 支持所有Windows系统打印机 / Supports all Windows system printers >> dist\README_Windows.txt
echo - 使用系统默认打印机 / Uses system default printer >> dist\README_Windows.txt
echo - 支持热敏小票打印机 / Supports thermal receipt printers >> dist\README_Windows.txt
echo. >> dist\README_Windows.txt
echo ## 故障排除 / Troubleshooting >> dist\README_Windows.txt
echo - 如果打印失败，请确保默认打印机设置正确 >> dist\README_Windows.txt
echo - 确保打印机在线并有纸张 >> dist\README_Windows.txt
echo - If printing fails, ensure default printer is configured correctly >> dist\README_Windows.txt
echo - Make sure printer is online and has paper >> dist\README_Windows.txt

:: 清理 / Cleanup
cd scripts
echo 📍 当前目录 / Current directory: %CD%
echo 🧹 清理构建环境 / Cleaning build environment...
call deactivate
rmdir /s /q build_venv
if exist build rmdir /s /q build
if exist __pycache__ rmdir /s /q __pycache__

echo.
echo ==================================================
echo ✅ Windows 版本构建完成！/ Windows build completed!
echo 📁 可执行文件位置 / Executable location: dist\PrintTheShot.exe
echo 📄 说明文件 / Readme: dist\README_Windows.txt
echo 🚀 启动方式 / Startup methods:
echo    - 双击运行 / Double-click: dist\PrintTheShot.exe
echo    - 使用脚本 / Using script: dist\start_server.bat
echo 📊 数据目录 / Data directories:
echo    - 冲泡数据 / Shot data: dist\shots_data\
echo    - 图表图片 / Chart images: dist\shots_images\
echo    - 插件文件 / Plugin files: dist\plugin\
echo ==================================================
echo ⏰ 构建完成时间 / Build completion time: %date% %time%
pause