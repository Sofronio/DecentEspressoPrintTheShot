#!/bin/bash

# 中英双语 macOS 构建脚本
# Bilingual macOS Build Script

echo " 开始构建 macOS 版本 / Starting macOS build..."
echo "=================================================="

# 检查是否为 macOS / Check if running on macOS
if [[ "$(uname)" != "Darwin" ]]; then
    echo "❌ 此脚本只能在 macOS 系统上运行"
    echo "❌ This script can only run on macOS systems"
    exit 1
fi

echo "📁 构建目录 / Build directory: $(pwd)"

# 检查 Python / Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python 3，请先安装 Python 3.8 或更高版本"
    echo "❌ Python 3 not found, please install Python 3.8 or higher"
    echo "💡 建议 / Recommendation: brew install python"
    exit 1
fi

# 检查 Homebrew / Check Homebrew
if ! command -v brew &> /dev/null; then
    echo "❌ 未找到 Homebrew，请先安装 Homebrew"
    echo "❌ Homebrew not found, please install Homebrew first"
    echo "💡 安装命令 / Installation command: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
fi

# 安装系统依赖 / Install system dependencies
echo "🔧 安装系统依赖 / Installing system dependencies..."
brew install freetype pkg-config libjpeg upx
echo "✅ 系统依赖安装完成 / System dependencies installed"

# 创建虚拟环境 / Create virtual environment
echo "📦 创建虚拟环境 / Creating virtual environment..."
python3 -m venv build_venv
source build_venv/bin/activate

# 安装依赖 / Install dependencies
echo "📥 安装依赖 / Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# 构建 / Build
echo "🏗️ 开始构建 / Starting build..."
cd ..
pyinstaller scripts/print_the_shot.spec
cd scripts

if [ $? -ne 0 ]; then
    echo "❌ PyInstaller 构建失败 / PyInstaller build failed"
    deactivate
    exit 1
fi

# 创建 macOS 应用包 / Create macOS application bundle
echo "📦 创建应用包 / Creating application bundle..."
mkdir -p "dist/PrintTheShotServer.app/Contents/MacOS"
mkdir -p "dist/PrintTheShotServer.app/Contents/Resources"

# 复制可执行文件 / Copy executable
echo "📦 复制可执行文件到应用包 / Copying executable to application bundle..."
cp ../dist/PrintTheShotServer "dist/PrintTheShotServer.app/Contents/MacOS/" 2>/dev/null || echo "⚠️  可执行文件复制失败，可能路径不正确 / Executable copy failed, path may be incorrect"

# 创建 Info.plist
cat > "dist/PrintTheShotServer.app/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>PrintTheShotServer</string>
    <key>CFBundleDisplayName</key>
    <string>PrintTheShotServer</string>
    <key>CFBundleIdentifier</key>
    <string>com.yourcompany.printtheshot</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleExecutable</key>
    <string>PrintTheShotServer</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>LSMinimumSystemVersion</key>
    <string>10.14</string>
</dict>
</plist>
EOF

# 创建启动脚本 / Create startup script
echo "📝 创建启动脚本 / Creating startup script..."
cat > ../dist/start_server.sh << 'EOF'
#!/bin/bash
# PrintTheShotServer 启动脚本 / Startup Script
echo "🍳 PrintTheShotServer 启动中 / Starting..."
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"
./PrintTheShotServer
EOF

chmod +x ../dist/start_server.sh 2>/dev/null || echo "⚠️  启动脚本权限设置失败 / Startup script permission set failed"

# 设置应用包执行权限 / Set application bundle executable permission
chmod +x "dist/PrintTheShotServer.app/Contents/MacOS/PrintTheShotServer"

# 清理 / Cleanup
echo "🧹 清理构建环境 / Cleaning build environment..."

# 1. 清理虚拟环境 / Cleanup virtual enviroment
deactivate
rm -rf build_venv
echo "✅ 虚拟环境已清理 / Virtual environment cleaned"

# 2. 清理 PyInstaller 临时构建文件 / Cleanup PyInstaller temp files
if [ -d "build" ]; then
    rm -rf build/
    echo "✅ PyInstaller 临时文件已清理 / PyInstaller temp files cleaned"
fi

# 3. 清理本地的临时 dist 文件 / Cleanup local temp dist files
if [ -d "dist" ]; then
    rm -rf dist/
    echo "✅ 本地临时构建文件已清理 / Local temp build files cleaned"
fi

echo ""
echo "=================================================="
echo "✅ macOS 版本构建完成！/ macOS build completed!"
echo "📁 可执行文件位置 / Executable location: dist/PrintTheShotServer"
echo "📦 应用包位置 / Application bundle: dist/PrintTheShotServer.app"
echo "🚀 启动方式 / Startup methods:"
echo "   - 直接运行 / Direct run: ./dist/PrintTheShotServer"
echo "   - 使用脚本 / Using script: ./dist/start_server.sh"
echo "   - 双击应用 / Double-click: dist/PrintTheShotServer.app"
echo "=================================================="