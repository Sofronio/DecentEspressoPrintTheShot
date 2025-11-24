# -*- mode: python ; coding: utf-8 -*-

import sys
import os
import matplotlib
from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

# 平台特定设置
if sys.platform == 'win32':
    icon = None  # 暂时禁用图标
elif sys.platform == 'darwin':
    icon = None  # 暂时禁用图标
else:
    icon = None

# 获取 matplotlib 数据文件
def get_matplotlib_data():
    try:
        mpl_data_path = matplotlib.get_data_path()
        print(f"🔍 Matplotlib data path: {mpl_data_path}")
        if os.path.exists(mpl_data_path):
            return [(mpl_data_path, 'matplotlib/mpl-data')]
        else:
            print("⚠️  Matplotlib data path not found, using empty list")
            return []
    except Exception as e:
        print(f"⚠️  Error getting matplotlib data: {e}")
        return []

# 分析阶段

# Windows特定的隐藏导入
windows_hiddenimports = []
if sys.platform == 'win32':
    windows_hiddenimports = [
        'win32print',
        'win32ui',
        'win32api', 
        'win32con',
        'pywintypes',
    ]

a = Analysis(
    ['../print_the_shot_server.py'],
    pathex=[os.getcwd(), '..'],
    binaries=[],
    datas=[],  # 暂时使用空列表，先让构建成功
    hiddenimports=[
        # matplotlib 相关
        'matplotlib.backends.backend_agg',
        'matplotlib.backends.backend_tkagg',
        'matplotlib.figure',
        'matplotlib.pyplot',
        'matplotlib._path',
        'matplotlib._png',
        'matplotlib.backend_bases',
        'matplotlib.backends.backend_svg',
        
        # PIL/Pillow 相关
        'PIL',
        'PIL._imaging',
        'PIL._imagingft',
        'PIL.Image',
        'PIL.ImageFile',
        'PIL.ImageOps',
        'PIL.ImageFilter',
        'PIL.ImageDraw',
        'PIL.ImageDraw2',
        
        # numpy 相关
        'numpy',
        'numpy.core._multiarray_umath',
        'numpy.core._dtype_ctypes',
        'numpy.lib.format',
        'numpy.random.common',
        'numpy.random.bounded_integers',
        'numpy.random.entropy',
        
        # 标准库隐藏导入
        'http.server',
        'socketserver',
        'urllib.parse',
        'email.mime.multipart',
        'email.mime.base',
        'email.mime.application',
        'email.mime.nonmultipart',
        'email.encoders',
        'html',
        'http.cookies',
        
        # 其他可能需要的模块
        'pkg_resources',
        'importlib_resources',
    ] + windows_hiddenimports,
    hookspath=[],
    hooksconfig={
        'matplotlib': {
            'hiddenimports': ['matplotlib.backends.backend_agg']
        },
        'PIL': {
            'hiddenimports': ['PIL._imaging', 'PIL._imagingft']
        }
    },
    runtime_hooks=[],
    excludes=[
        'tkinter',  # 如果不使用 GUI
        'test',
        'unittest',
        'pydoc',
        'pdb',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# PY2 归档
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# 可执行文件配置
if sys.platform == 'win32':
    console = True
elif sys.platform == 'darwin':
    console = False  # macOS 通常不显示控制台
else:
    console = True

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='PrintTheShot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # 使用 UPX 压缩
    upx_exclude=[],
    runtime_tmpdir=None,
    console=console,
    disable_windowed_traceback=False,
    argv_emulation=False if sys.platform != 'darwin' else True,
    target_arch=None,
    codesign_identity=None,
    entitle_file=None,
    icon=icon,
)

# 如果需要创建目录
def mkdirs():
    dirs = ['shots_data', 'shots_images', 'plugin']
    for dir_name in dirs:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)

# 构建后脚本
def post_build():
    # mkdirs()
    print("✅ 构建完成！可执行文件在 dist/ 目录")
    print("📁 必要的目录已创建")

# 注册后构建步骤
import atexit
atexit.register(post_build)