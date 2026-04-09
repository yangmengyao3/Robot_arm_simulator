import sys
print("Python 版本:", sys.version)
print("Python 路径:", sys.executable)
print()

# 检查必需的包
required_packages = ['matplotlib', 'numpy', 'PyQt5', 'pyinstaller']

for package in required_packages:
    try:
        mod = __import__(package)
        version = getattr(mod, '__version__', '未知版本')
        print(f"✅ {package} 已安装 (版本：{version})")
    except ImportError:
        print(f"❌ {package} 未安装")

print()
print("=" * 50)

# 检查 matplotlib 数据路径
try:
    import matplotlib
    print("Matplotlib 数据路径:", matplotlib.get_data_path())
except ImportError:
    print("无法获取 Matplotlib 数据路径（未安装）")