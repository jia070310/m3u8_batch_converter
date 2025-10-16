import PyInstaller.__main__
import os
import shutil
from pathlib import Path

def create_proper_icon():
    """创建符合要求的图标"""
    try:
        from PIL import Image, ImageDraw
        
        os.makedirs('resources', exist_ok=True)
        
        print("正在创建符合要求的图标...")
        
        # 定义标准尺寸
        sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        
        # 创建图标图像列表
        icon_images = []
        
        for size in sizes:
            img = Image.new('RGBA', size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # 绘制蓝色圆形背景
            margin = max(2, size[0] // 16)
            draw.ellipse([margin, margin, size[0]-margin, size[1]-margin], 
                        fill=(0, 120, 212, 255))
            
            # 绘制播放三角形（只在较大尺寸上绘制）
            if size[0] >= 32:
                triangle_margin = size[0] // 5
                triangle_points = [
                    (triangle_margin, triangle_margin),
                    (triangle_margin, size[1] - triangle_margin),
                    (size[0] - triangle_margin, size[1] // 2)
                ]
                draw.polygon(triangle_points, fill=(255, 255, 255, 255))
            
            icon_images.append(img)
        
        # 保存为ICO
        icon_path = Path('resources') / 'icon.ico'
        icon_images[0].save(icon_path, format='ICO', sizes=[s[0] for s in sizes], 
                           append_images=icon_images[1:])
        
        print(f"✅ 图标已创建: {icon_path}")
        return str(icon_path)
        
    except ImportError:
        print("⚠️  Pillow未安装，使用备用方案")
        return create_simple_icon_fallback()

def create_simple_icon_fallback():
    """备用方案：使用系统工具创建图标"""
    import subprocess
    try:
        # 尝试使用在线图标或现有图标
        icon_path = Path('resources') / 'icon.ico'
        if not icon_path.exists():
            print("💡 请手动将 icon.ico 文件放入 resources 文件夹")
            return None
        return str(icon_path)
    except:
        return None

def check_ffmpeg():
    """检查FFmpeg是否存在"""
    ffmpeg_path = Path('resources') / 'ffmpeg.exe'
    if ffmpeg_path.exists():
        print(f"✅ 找到FFmpeg: {ffmpeg_path}")
        return True
    else:
        print(f"⚠️  未找到FFmpeg: {ffmpeg_path}")
        return False

def main():
    print("🔧 准备打包 M3U8 批量视频分割工具...")
    
    # 创建资源目录
    os.makedirs('resources', exist_ok=True)
    
    # 创建或检查图标
    icon_path = None
    if Path('resources/icon.ico').exists():
        icon_path = 'resources/icon.ico'
        print("✅ 使用现有图标")
    else:
        icon_path = create_proper_icon()
    
    # 检查FFmpeg
    ffmpeg_exists = check_ffmpeg()
    
    if not icon_path:
        print("❌ 未找到图标文件，程序将使用默认图标")
        cmd = [
            'm3u8_batch_converter.py',
            '--name=M3U8批量视频分割工具',
            '--onedir',
            '--windowed',
            '--clean',
            '--noconfirm',
            '--hidden-import=concurrent.futures',
            '--hidden-import=queue',
            '--hidden-import=tkinter',
        ]
    else:
        print(f"🎯 使用图标: {icon_path}")
        
        # 构建PyInstaller命令 - 关键修改：确保图标正确嵌入
        cmd = [
            'm3u8_batch_converter.py',
            '--name=M3U8批量视频分割工具',
            '--onedir',
            '--windowed',
            '--clean',
            '--noconfirm',
            f'--icon={icon_path}',  # 关键：直接指定图标路径
            '--hidden-import=concurrent.futures',
            '--hidden-import=queue',
            '--hidden-import=tkinter',
        ]
    
    print("🚀 开始打包过程...")
    try:
        PyInstaller.__main__.run(cmd)
        print("✅ PyInstaller打包完成！")
        
        # 复制ffmpeg到输出目录
        if ffmpeg_exists:
            ffmpeg_src = Path('resources') / 'ffmpeg.exe'
            ffmpeg_dest = Path('dist') / 'M3U8批量视频分割工具' / 'ffmpeg.exe'
            ffmpeg_dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ffmpeg_src, ffmpeg_dest)
            print("✅ FFmpeg 已复制到输出目录")
        
        # 复制图标到输出目录（确保程序能找到）
        if icon_path:
            icon_dest = Path('dist') / 'M3U8批量视频分割工具' / 'icon.ico'
            shutil.copy2(icon_path, icon_dest)
            print("✅ 图标文件已复制到输出目录")
        
        print("\n📁 程序位置: dist/M3U8批量视频分割工具/")
        print("🎉 现在可以运行 create_installer.py 创建安装程序")
        
        # 验证图标是否嵌入
        verify_icon_embedded()
        
    except Exception as e:
        print(f"❌ 打包失败: {e}")

def verify_icon_embedded():
    """验证图标是否已嵌入可执行文件"""
    exe_path = Path('dist') / 'M3U8批量视频分割工具' / 'M3U8批量视频分割工具.exe'
    if exe_path.exists():
        print("🔍 检查可执行文件图标...")
        try:
            # 简单的文件大小检查
            file_size = exe_path.stat().st_size
            if file_size > 5000000:  # 如果文件大于5MB，可能包含图标
                print("✅ 可执行文件可能已包含图标")
            else:
                print("⚠️  可执行文件较小，图标可能未正确嵌入")
        except:
            print("ℹ️  无法验证图标嵌入状态")

if __name__ == "__main__":
    main()