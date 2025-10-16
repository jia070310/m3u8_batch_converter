import os
import sys
import subprocess
import threading
from pathlib import Path
from datetime import datetime
import concurrent.futures

# 修复控制台窗口问题
if sys.platform == "win32":
    import ctypes
    # 隐藏控制台窗口
    whnd = ctypes.windll.kernel32.GetConsoleWindow()
    if whnd != 0:
        ctypes.windll.user32.ShowWindow(whnd, 0)

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    from tkinter.scrolledtext import ScrolledText
except ImportError:
    print("请安装 tkinter 库")
    sys.exit(1)

class M3U8Converter:
    def __init__(self, ffmpeg_path=None):
        if ffmpeg_path is None:
            self.ffmpeg_path = self.find_ffmpeg()
        else:
            self.ffmpeg_path = ffmpeg_path
            
        self.is_running = False
        self.current_process = None
        
    def find_ffmpeg(self):
        """自动查找 ffmpeg 可执行文件 - 优化版本"""
        possible_paths = []
        
        # 1. 检查打包后的环境
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
            possible_paths.append(os.path.join(base_dir, 'ffmpeg.exe'))
            
            if hasattr(sys, '_MEIPASS'):
                possible_paths.append(os.path.join(sys._MEIPASS, 'ffmpeg.exe'))
        
        # 2. 检查开发环境
        script_dir = os.path.dirname(os.path.abspath(__file__))
        possible_paths.append(os.path.join(script_dir, 'resources', 'ffmpeg.exe'))
        possible_paths.append(os.path.join(script_dir, 'ffmpeg.exe'))
        
        # 3. 检查路径
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # 4. 检查系统PATH
        try:
            # 使用不显示窗口的方式检查
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0
            
            subprocess.run(["ffmpeg", "-version"], 
                         capture_output=True, 
                         check=True,
                         startupinfo=startupinfo)
            return "ffmpeg"
        except:
            pass
                
        return "ffmpeg"
    
    def check_ffmpeg(self):
        """检查 ffmpeg 是否可用"""
        try:
            # 隐藏ffmpeg检查时的窗口
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0
            
            result = subprocess.run([self.ffmpeg_path, "-version"], 
                                  capture_output=True, 
                                  check=True,
                                  startupinfo=startupinfo)
            return True, f"FFmpeg 检测成功: {self.ffmpeg_path}"
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False, "未找到 FFmpeg，请确保已安装并添加到系统PATH中"
    
    def convert_to_m3u8_optimized(self, input_file, output_dir, segment_duration=10, 
                                output_filename=None, log_callback=None, task_id=None):
        """优化的视频转换方法"""
        try:
            self.is_running = True
            input_path = Path(input_file)
            output_path = Path(output_dir)
            
            output_path.mkdir(parents=True, exist_ok=True)
            
            if not output_filename:
                output_filename = input_path.stem
            
            m3u8_file = output_path / f"{output_filename}.m3u8"
            ts_pattern = output_path / f"{output_filename}_%03d.ts"
            
            if log_callback:
                log_callback(f"[任务{task_id}] 开始转换: {input_path.name}", task_id)
            
            # 构建优化的FFmpeg命令
            cmd = [
                self.ffmpeg_path,
                "-i", str(input_path),
                "-c", "copy",
                "-f", "hls",
                "-hls_time", str(segment_duration),
                "-hls_list_size", "0",
                "-hls_segment_filename", str(ts_pattern),
                "-avoid_negative_ts", "make_zero",
                "-fflags", "+genpts",
                "-y",
                str(m3u8_file)
            ]
            
            # 隐藏FFmpeg窗口
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0
            
            # 执行转换
            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=False,
                bufsize=8192,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # 快速读取输出
            output, _ = self.current_process.communicate()
            
            return_code = self.current_process.wait()
            
            if return_code == 0 and self.is_running:
                m3u8_exists = m3u8_file.exists()
                ts_files = list(output_path.glob(f"{output_filename}_*.ts"))
                
                if m3u8_exists and ts_files:
                    success_msg = f"转换成功！生成 {len(ts_files)} 个TS片段"
                    if log_callback:
                        log_callback(f"[任务{task_id}] ✅ {success_msg}", task_id)
                    return True, success_msg
                else:
                    error_msg = "转换完成但未生成预期文件"
                    if log_callback:
                        log_callback(f"[任务{task_id}] ❌ {error_msg}", task_id)
                    return False, error_msg
            else:
                error_msg = f"转换失败，返回码: {return_code}"
                if log_callback:
                    log_callback(f"[任务{task_id}] ❌ {error_msg}", task_id)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"转换过程中出错: {str(e)}"
            if log_callback:
                log_callback(f"[任务{task_id}] ❌ {error_msg}", task_id)
            return False, error_msg
        finally:
            self.is_running = False
            self.current_process = None
    
    def stop_conversion(self):
        """停止转换过程"""
        self.is_running = False
        if self.current_process:
            self.current_process.terminate()
            try:
                self.current_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.current_process.kill()

class M3U8BatchConverterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("M3U8 批量视频分割工具 v2.0")
        self.root.geometry("1200x800")
        
        # 设置程序图标 - 新增代码
        self.set_window_icon()
        
        # 初始化变量
        self.video_files = []
        self.conversion_tasks = []
        self.is_converting = False
        self.file_paths = {}
        self.max_workers = min(4, (os.cpu_count() or 1))
        self.completed_tasks = 0
        self.submitted_tasks = 0
        self.task_results = {}
        
        # 设置界面
        self.setup_ui()
        
        # 启动时检查 FFmpeg
        self.check_ffmpeg_on_startup()
    
    def set_window_icon(self):
        """设置窗口图标"""
        try:
            # 方法1: 尝试从ICO文件加载
            icon_path = self.find_icon_file()
            if icon_path and os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
                print(f"✅ 已设置程序图标: {icon_path}")
                return
            
            # 方法2: 尝试从可执行文件资源加载（打包后）
            if getattr(sys, 'frozen', False):
                # 打包环境：尝试从exe文件加载图标
                exe_path = sys.executable
                self.root.iconbitmap(exe_path)
                print("✅ 已使用可执行文件图标")
                return
                
            # 方法3: 使用默认图标或创建空图标
            self.root.iconbitmap(default="")
            print("ℹ️  使用默认图标")
            
        except Exception as e:
            print(f"⚠️  设置图标失败: {e}")
            # 设置空图标作为后备
            try:
                self.root.iconbitmap(default="")
            except:
                pass

    def find_icon_file(self):
        """查找图标文件"""
        possible_paths = []
        
        # 打包环境
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
            possible_paths.extend([
                os.path.join(base_dir, 'icon.ico'),
                os.path.join(base_dir, 'resources', 'icon.ico'),
                os.path.join(base_dir, '_internal', 'icon.ico')
            ])
            
            if hasattr(sys, '_MEIPASS'):
                possible_paths.append(os.path.join(sys._MEIPASS, 'icon.ico'))
        
        # 开发环境
        script_dir = os.path.dirname(os.path.abspath(__file__))
        possible_paths.extend([
            os.path.join(script_dir, 'icon.ico'),
            os.path.join(script_dir, 'resources', 'icon.ico'),
            os.path.join(script_dir, '..', 'resources', 'icon.ico')
        ])
        
        # 检查所有可能的路径
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    
    def setup_ui(self):
        """设置用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧视频列表框架
        left_frame = ttk.LabelFrame(main_frame, text="视频文件列表", padding="10")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # 右侧控制和日志框架
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 设置各个部分
        self.setup_video_list(left_frame)
        self.setup_control_panel(right_frame)
        self.setup_log_panel(right_frame)
    
    def setup_video_list(self, parent):
        """设置视频列表界面"""
        # 按钮框架
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(button_frame, text="添加文件", command=self.add_files).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="添加文件夹", command=self.add_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="移除选中", command=self.remove_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="清空列表", command=self.clear_list).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="全选", command=self.select_all).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="取消全选", command=self.deselect_all).pack(side=tk.RIGHT, padx=5)
        
        # 视频列表
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("选择", "文件名", "大小", "状态")
        self.video_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        self.video_tree.heading("选择", text="✓")
        self.video_tree.heading("文件名", text="文件名")
        self.video_tree.heading("大小", text="文件大小")
        self.video_tree.heading("状态", text="状态")
        
        self.video_tree.column("选择", width=40, anchor="center")
        self.video_tree.column("文件名", width=250)
        self.video_tree.column("大小", width=100, anchor="center")
        self.video_tree.column("状态", width=80, anchor="center")
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.video_tree.yview)
        self.video_tree.configure(yscrollcommand=scrollbar.set)
        
        self.video_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.video_tree.bind("<Double-1>", self.on_item_double_click)
    
    def setup_control_panel(self, parent):
        """设置控制面板"""
        control_frame = ttk.LabelFrame(parent, text="转换设置", padding="10")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 输出目录
        output_frame = ttk.Frame(control_frame)
        output_frame.pack(fill=tk.X, pady=5)
        ttk.Label(output_frame, text="输出目录:").pack(side=tk.LEFT)
        
        output_input_frame = ttk.Frame(output_frame)
        output_input_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 5))
        self.output_entry = ttk.Entry(output_input_frame)
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(output_input_frame, text="浏览", command=self.browse_output_dir, width=8).pack(side=tk.RIGHT, padx=(5, 0))
        
        # 片段时长
        duration_frame = ttk.Frame(control_frame)
        duration_frame.pack(fill=tk.X, pady=5)
        ttk.Label(duration_frame, text="TS片段时长:").pack(side=tk.LEFT)
        self.duration_entry = ttk.Entry(duration_frame, width=10)
        self.duration_entry.insert(0, "10")
        self.duration_entry.pack(side=tk.LEFT, padx=(10, 5))
        ttk.Label(duration_frame, text="秒").pack(side=tk.LEFT)
        
        # 并行任务
        parallel_frame = ttk.Frame(control_frame)
        parallel_frame.pack(fill=tk.X, pady=5)
        ttk.Label(parallel_frame, text="并行任务数:").pack(side=tk.LEFT)
        self.parallel_var = tk.StringVar(value=str(self.max_workers))
        parallel_spinbox = ttk.Spinbox(parallel_frame, from_=1, to=min(8, self.max_workers * 2), 
                                     textvariable=self.parallel_var, width=5)
        parallel_spinbox.pack(side=tk.LEFT, padx=(10, 5))
        
        # 控制按钮
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.start_selected_btn = ttk.Button(button_frame, text="开始转换选中项", 
                                           command=self.start_selected_conversion, width=18)
        self.start_selected_btn.pack(side=tk.LEFT, padx=5)
        
        self.start_all_btn = ttk.Button(button_frame, text="开始转换全部", 
                                      command=self.start_all_conversion, width=18)
        self.start_all_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(button_frame, text="停止转换", 
                                 command=self.stop_conversion, state=tk.DISABLED, width=18)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # 进度显示
        progress_frame = ttk.Frame(control_frame)
        progress_frame.pack(fill=tk.X, pady=5)
        ttk.Label(progress_frame, text="总体进度:").pack(side=tk.LEFT)
        self.progress_label = ttk.Label(progress_frame, text="0/0")
        self.progress_label.pack(side=tk.LEFT, padx=(10, 0))
        
        self.overall_progress = ttk.Progressbar(control_frame, mode='determinate')
        self.overall_progress.pack(fill=tk.X, pady=5)
        
        # 并行任务状态
        parallel_status_frame = ttk.Frame(control_frame)
        parallel_status_frame.pack(fill=tk.X, pady=5)
        ttk.Label(parallel_status_frame, text="运行中任务:").pack(side=tk.LEFT)
        self.parallel_status_label = ttk.Label(parallel_status_frame, text="0")
        self.parallel_status_label.pack(side=tk.LEFT, padx=(10, 0))
    
    def setup_log_panel(self, parent):
        """设置日志面板"""
        log_frame = ttk.LabelFrame(parent, text="转换日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = ScrolledText(log_frame, width=80, height=20, state=tk.DISABLED, font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
    
    def check_ffmpeg_on_startup(self):
        """启动时检查 FFmpeg"""
        self.converter = M3U8Converter()
        success, message = self.converter.check_ffmpeg()
        if success:
            self.log_message(f"✅ {message}")
        else:
            self.log_message(f"⚠️ {message}")
    
    def add_files(self):
        """添加文件到列表"""
        filetypes = [
            ("所有视频文件", "*.mp4 *.mkv *.avi *.mov *.wmv *.flv *.webm *.m4v *.3gp *.ts *.m2ts"),
            ("所有文件", "*.*")
        ]
        
        files = filedialog.askopenfilenames(title="选择视频文件", filetypes=filetypes)
        if files:
            added_count = 0
            for file in files:
                if self.add_video_to_list(file):
                    added_count += 1
            self.log_message(f"✅ 成功添加 {added_count} 个文件")
    
    def add_folder(self):
        """添加文件夹"""
        folder = filedialog.askdirectory(title="选择视频文件夹")
        if folder:
            video_extensions = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp', '.ts', '.m2ts'}
            folder_path = Path(folder)
            added_count = 0
            for file_path in folder_path.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in video_extensions:
                    if self.add_video_to_list(str(file_path)):
                        added_count += 1
            if added_count > 0:
                self.log_message(f"✅ 成功添加 {added_count} 个文件")
    
    def add_video_to_list(self, file_path):
        """添加视频到列表"""
        try:
            abs_path = os.path.abspath(file_path)
            for item_id in self.video_tree.get_children():
                if item_id in self.file_paths and self.file_paths[item_id] == abs_path:
                    return False
            
            file_size = os.path.getsize(abs_path)
            size_str = self.format_file_size(file_size)
            self.video_files.append(abs_path)
            path = Path(file_path)
            
            item_id = self.video_tree.insert("", tk.END, values=("✓", path.name, size_str, "等待"))
            self.file_paths[item_id] = abs_path
            return True
        except Exception as e:
            self.log_message(f"❌ 添加文件失败 {file_path}: {str(e)}")
            return False
    
    def format_file_size(self, size_bytes):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def remove_selected(self):
        """移除选中项"""
        selected_items = self.video_tree.selection()
        if selected_items:
            for item in selected_items:
                if item in self.file_paths:
                    file_path = self.file_paths[item]
                    if file_path in self.video_files:
                        self.video_files.remove(file_path)
                    del self.file_paths[item]
                self.video_tree.delete(item)
            self.log_message(f"✅ 已移除 {len(selected_items)} 个文件")
    
    def clear_list(self):
        """清空列表"""
        if self.video_tree.get_children():
            self.video_tree.delete(*self.video_tree.get_children())
            self.video_files.clear()
            self.file_paths.clear()
            self.log_message("✅ 已清空文件列表")
    
    def select_all(self):
        """全选"""
        for item in self.video_tree.get_children():
            self.video_tree.set(item, "选择", "✓")
    
    def deselect_all(self):
        """取消全选"""
        for item in self.video_tree.get_children():
            self.video_tree.set(item, "选择", "")
    
    def on_item_double_click(self, event):
        """双击切换选择"""
        item = self.video_tree.identify_row(event.y)
        if item:
            current_value = self.video_tree.set(item, "选择")
            new_value = "✓" if current_value == "" else ""
            self.video_tree.set(item, "选择", new_value)
    
    def browse_output_dir(self):
        """浏览输出目录"""
        directory = filedialog.askdirectory(title="选择输出目录")
        if directory:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, directory)
    
    def get_selected_videos(self):
        """获取选中的视频"""
        selected_videos = []
        for item in self.video_tree.get_children():
            if self.video_tree.set(item, "选择") == "✓":
                if item in self.file_paths:
                    file_path = self.file_paths[item]
                    selected_videos.append((item, file_path))
        return selected_videos
    
    def start_selected_conversion(self):
        """开始转换选中项"""
        selected = self.get_selected_videos()
        if not selected:
            messagebox.showwarning("警告", "请先选择要转换的视频文件")
            return
        output_dir = self.output_entry.get().strip()
        if not output_dir:
            messagebox.showerror("错误", "请选择输出目录")
            return
        self.start_conversion(selected)
    
    def start_all_conversion(self):
        """开始转换全部"""
        all_videos = []
        for item in self.video_tree.get_children():
            if item in self.file_paths:
                file_path = self.file_paths[item]
                all_videos.append((item, file_path))
        if not all_videos:
            messagebox.showwarning("警告", "视频列表为空")
            return
        output_dir = self.output_entry.get().strip()
        if not output_dir:
            messagebox.showerror("错误", "请选择输出目录")
            return
        self.start_conversion(all_videos)
    
    def start_conversion(self, task_list):
        """开始转换"""
        output_dir = self.output_entry.get().strip()
        duration_str = self.duration_entry.get().strip()
        
        if not output_dir:
            messagebox.showerror("错误", "请设置输出目录")
            return
        
        try:
            segment_duration = int(duration_str)
            if segment_duration <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("错误", "请输入有效的片段时长")
            return
        
        try:
            parallel_tasks = int(self.parallel_var.get())
            parallel_tasks = max(1, min(parallel_tasks, self.max_workers * 2))
        except:
            parallel_tasks = self.max_workers
        
        output_path = Path(output_dir)
        if not output_path.exists():
            try:
                output_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                messagebox.showerror("错误", f"无法创建输出目录: {e}")
                return
        
        # 重置状态
        self.completed_tasks = 0
        self.submitted_tasks = 0
        self.task_results = {}
        self.conversion_tasks = []
        
        for item, file_path in task_list:
            path = Path(file_path)
            task_output_dir = output_path / path.stem
            self.conversion_tasks.append({
                'item': item,
                'file_path': file_path,
                'output_dir': str(task_output_dir),
                'segment_duration': segment_duration,
                'output_filename': path.stem
            })
            self.video_tree.set(item, "状态", "等待")
        
        self.is_converting = True
        self.start_selected_btn.config(state=tk.DISABLED)
        self.start_all_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        self.overall_progress.config(maximum=len(self.conversion_tasks), value=0)
        self.progress_label.config(text=f"0/{len(self.conversion_tasks)}")
        self.parallel_status_label.config(text="0")
        
        self.log_message("🚀 开始批量转换...")
        self.log_message(f"📋 总任务数: {len(self.conversion_tasks)}")
        
        # 创建线程池并提交任务
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=parallel_tasks)
        self.futures = {}
        
        for task_index, task in enumerate(self.conversion_tasks):
            future = self.submit_single_task(task, task_index + 1)
            if future:
                self.futures[future] = task_index
                self.submitted_tasks += 1
        
        self.monitor_tasks()
    
    def submit_single_task(self, task, task_id):
        """提交单个任务"""
        if not self.is_converting:
            return None
        
        file_name = Path(task['file_path']).name
        self.video_tree.set(task['item'], "状态", "转换中")
        self.log_message(f"🔧 提交任务 {task_id}/{len(self.conversion_tasks)}: {file_name}")
        
        try:
            future = self.executor.submit(self.run_single_task_optimized, task, task_id)
            future.add_done_callback(self.task_finished_callback)
            return future
        except Exception as e:
            self.log_message(f"❌ 提交任务失败: {str(e)}")
            self.video_tree.set(task['item'], "状态", "失败")
            return None
    
    def run_single_task_optimized(self, task, task_id):
        """运行单个任务"""
        converter = M3U8Converter()
        success, message = converter.convert_to_m3u8_optimized(
            input_file=task['file_path'],
            output_dir=task['output_dir'],
            segment_duration=task['segment_duration'],
            output_filename=task['output_filename'],
            log_callback=self.log_message,
            task_id=task_id
        )
        return task, task_id, success, message
    
    def task_finished_callback(self, future):
        """任务完成回调"""
        if not self.is_converting:
            return
        try:
            task, task_id, success, message = future.result()
            self.root.after(0, self.handle_task_result, task, task_id, success, message)
        except Exception as e:
            self.log_message(f"❌ 任务执行异常: {str(e)}")
    
    def handle_task_result(self, task, task_id, success, message):
        """处理任务结果"""
        if not self.is_converting:
            return
        
        status = "成功" if success else "失败"
        self.video_tree.set(task['item'], "状态", status)
        self.task_results[task_id] = (success, message)
        self.completed_tasks += 1
        
        self.overall_progress.config(value=self.completed_tasks)
        self.progress_label.config(text=f"{self.completed_tasks}/{len(self.conversion_tasks)}")
        
        running_count = self.submitted_tasks - self.completed_tasks
        self.parallel_status_label.config(text=str(running_count))
    
    def monitor_tasks(self):
        """监控任务状态"""
        if not self.is_converting:
            return
        if self.completed_tasks >= len(self.conversion_tasks):
            self.finalize_conversion()
        else:
            self.root.after(1000, self.monitor_tasks)
    
    def finalize_conversion(self):
        """完成转换"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)
        
        self.is_converting = False
        self.start_selected_btn.config(state=tk.NORMAL)
        self.start_all_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        
        success_count = sum(1 for result in self.task_results.values() if result[0])
        self.log_message("🎉 批量转换完成！")
        self.log_message(f"📊 转换结果: 成功 {success_count}/{len(self.conversion_tasks)}")
        
        messagebox.showinfo("完成", f"批量转换完成！\n成功: {success_count}/{len(self.conversion_tasks)}")
    
    def stop_conversion(self):
        """停止转换"""
        self.is_converting = False
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
        
        for task in self.conversion_tasks:
            if self.video_tree.set(task['item'], "状态") in ["等待", "转换中"]:
                self.video_tree.set(task['item'], "状态", "已停止")
        
        self.start_selected_btn.config(state=tk.NORMAL)
        self.start_all_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.log_message("⏹️ 用户停止转换")
    
    def log_message(self, message, task_id=None):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, formatted_message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

def main():
    # 设置高DPI
    if sys.platform == "win32":
        from ctypes import windll
        try:
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
    
    root = tk.Tk()
    app = M3U8BatchConverterGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()