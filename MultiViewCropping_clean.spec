# MultiViewCropping - 干净修复版打包配置
# 修复了以下所有问题：
# 1. 移除了错误的 from PyInstaller.building.build_main import Analysis, PYZ, EXE
# 2. 移除了硬编码绝对路径的 runtime_hooks
# 3. 修复了 datas 重复包含（binaries vs datas 冲突）
# 4. 移除了不存在的 PKG() 调用
# 5. 先用 console=True 方便调试，确认正常后改为 False

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# ── 隐藏导入 ──────────────────────────────────────────────
hiddenimports = collect_submodules('cv2')
hiddenimports += collect_submodules('numpy')
hiddenimports += collect_submodules('PIL')
hiddenimports += [
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'PySide6.QtSvg',
    'PySide6.QtOpenGL',
    'shiboken6',
    'xml.parsers.expat',
    'plistlib',
    'pkg_resources',
    'encodings',
    'xml.etree',
    'xml.etree.ElementTree',
]

# ── 数据文件：收集 PySide6 的所有插件（关键！含 qwindows.dll）──
datas = collect_data_files('PySide6', subdir='plugins')
datas += collect_data_files('shiboken6')

# ── 分析阶段 ──────────────────────────────────────────────
a = Analysis(
    ['main.py'],
    pathex=[r'C:\Users\Lin\MultiViewCropping'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],   # 不写硬编码路径
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

# ── EXE（onedir 模式，先开 console 调试）────────────────
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MultiViewCropping',
    debug=False,
    strip=False,
    upx=False,
    console=True,   # ← 先 True，能看到启动日志；确认无误后改 False
    disable_windowed_traceback=False,
)

# ── COLLECT（onedir 输出目录）────────────────────────────
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='MultiViewCropping',
)
