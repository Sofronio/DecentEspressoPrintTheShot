#!/bin/bash

# 中英双语 Linux 构建脚本
# Bilingual Linux Build Script

echo "🐧 开始构建 Linux 版本 / Starting Linux build..."
echo "=================================================="

# 检查是否为 Linux / Check if running on Linux
if [[ "$(uname)" != "Linux" ]]; then
    echo "❌ 此脚本只能在 Linux 系统上运行"
    echo "❌ This script can only run on Linux systems"
    exit 1
fi

echo "📁 构建目录 / Build directory: $(pwd)"

# 检查 Python / Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python 3，请先安装 Python 3.8 或更高版本"
    echo "❌ Python 3 not found, please install Python 3.8 or higher"
    exit 1
fi

# 创建虚拟环境 / Create virtual environment
echo "📦 创建虚拟环境 / Creating virtual environment..."
python3 -m venv build_venv
source build_venv/bin/activate

# 安装依赖 / Install dependencies
echo "📥 安装依赖 / Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# 安装系统依赖 (Ubuntu/Debian) / Install system dependencies
echo "🔧 安装系统依赖 / Installing system dependencies..."
if command -v apt-get &> /dev/null; then
    echo "🔄 更新包列表 / Updating package list..."
    sudo apt-get update
    echo "📦 安装开发工具 / Installing development tools..."
    sudo apt-get install -y \
        python3-dev \
        build-essential \
        libfreetype6-dev \
        libpng-dev \
        libjpeg-dev \
        upx
    echo "✅ 系统依赖安装完成 / System dependencies installed"
else
    echo "⚠️  非 Debian/Ubuntu 系统，请手动安装依赖"
    echo "⚠️  Non-Debian/Ubuntu system, please install dependencies manually"
    echo "💡 需要 / Required: python3-dev, build-essential, libfreetype6-dev, libpng-dev, libjpeg-dev, upx"
fi

# 确保必要的目录存在 / Ensure necessary directories exist
echo "📁 创建必要目录 / Creating necessary directories..."
mkdir -p shots_data shots_images plugin assets

# 构建 / Build
echo "🏗️ 开始构建 / Starting build..."
cd ..
cd scripts
pyinstaller print_the_shot.spec
cd ..
cd build

if [ $? -ne 0 ]; then
    echo "❌ PyInstaller 构建失败 / PyInstaller build failed"
    deactivate
    exit 1
fi

# 创建启动脚本 / Create startup script
echo "📝 创建启动脚本 / Creating startup script..."
cat > dist/start_server.sh << 'EOF'
#!/bin/bash
# PrintTheShot Server 启动脚本 / Startup Script
echo "🍳 PrintTheShot Server 启动中 / Starting..."
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"
./PrintTheShot_Server
EOF

chmod +x dist/start_server.sh

# 清理 / Cleanup
echo "🧹 清理构建环境 / Cleaning build environment..."
deactivate
rm -rf build_venv
rm -rf build/

echo ""
echo "=================================================="
echo "✅ Linux 版本构建完成！/ Linux build completed!"
echo "📁 可执行文件位置 / Executable location: dist/PrintTheShot_Server"
echo "🚀 启动方式 / Startup methods:"
echo "   - 直接运行 / Direct run: ./dist/PrintTheShot_Server"
echo "   - 使用脚本 / Using script: ./dist/start_server.sh"
echo "=================================================="