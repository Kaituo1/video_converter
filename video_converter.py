import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import os
import sys
import re

class VideoConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("视频格式转换器v1.2.0")
        self.root.geometry("750x1280")
        self.root.resizable(False, False)  # 不允许调整大小
        
        # 支持的输出格式
        self.output_formats = [
            "MP4", "MKV", "AVI", "WMV", "MOV", 
            "FLV", "MPEG", "3GP"
        ]
        
        # 默认使用高质量输出
        self.quality_params = "-crf 18 -preset slow"
        
        # 检查FFmpeg
        self.ffmpeg_path = self.find_ffmpeg()
        if not self.ffmpeg_path:
            import webbrowser
            answer = messagebox.askyesno(
                "未找到FFmpeg", 
                "未找到FFmpeg，请确保已安装FFmpeg并添加到系统PATH。\n\n是否跳转到FFmpeg官网下载？"
            )
            if answer:
                # 跳转到FFmpeg官网
                webbrowser.open("https://ffmpeg.org/download.html")
            self.root.destroy()
            return
        
        # 创建界面
        self.create_widgets()
    
    def find_ffmpeg(self):
        """查找FFmpeg可执行文件"""
        try:
            # 尝试直接运行ffmpeg命令
            subprocess.run(["ffmpeg", "-version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return "ffmpeg"
        except (subprocess.CalledProcessError, FileNotFoundError):
            # 尝试在当前目录查找
            if sys.platform.startswith("win"):
                ffmpeg_exe = "ffmpeg.exe"
            else:
                ffmpeg_exe = "ffmpeg"
            
            if os.path.exists(ffmpeg_exe):
                return ffmpeg_exe
            if os.path.exists(os.path.join(os.getcwd(), ffmpeg_exe)):
                return os.path.join(os.getcwd(), ffmpeg_exe)
            
            return None
    
    def detect_gpus(self):
        """检测系统中的GPU显卡信息（仅支持Windows）"""
        gpus = []
        
        try:
            # 仅保留Windows系统检测显卡
            if sys.platform == 'win32':
                # Windows系统检测显卡
                result = subprocess.run(
                    ["wmic", "path", "win32_VideoController", "get", "name"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                # 解析输出
                for line in result.stdout.strip().split('\n')[1:]:
                    line = line.strip()
                    if line:
                        gpus.append(line)
        
        except Exception as e:
            print(f"检测显卡时出错: {e}")
        
        return gpus
    
    def get_optimal_gpu_accel(self):
        """根据检测到的GPU选择最优的加速选项"""
        gpus = self.detect_gpus()
        
        # 定义显卡优先级：NVIDIA > AMD > Intel
        if any('nvidia' in gpu.lower() for gpu in gpus):
            return "NVIDIA CUDA"
        elif any('amd' in gpu.lower() or 'radeon' in gpu.lower() for gpu in gpus):
            return "AMD VCE"
        elif any('intel' in gpu.lower() or 'hd graphics' in gpu.lower() or 'iris' in gpu.lower() for gpu in gpus):
            return "Intel QSV"
        else:
            # 未检测到支持的GPU，使用自动模式
            return "自动"
    
    def create_widgets(self):
        """创建GUI界面组件"""
        # 设置窗口样式
        self.root.configure(bg="#2c3e50")
        
        # 标题
        title_frame = tk.Frame(self.root, bg="#34495e", bd=0)
        title_frame.pack(fill=tk.X, padx=0, pady=0)
        
        title_label = tk.Label(
            title_frame, 
            text="视频格式转换器", 
            font=("微软雅黑", 20, "bold"),
            bg="#34495e",
            fg="#ffffff"
        )
        title_label.pack(anchor=tk.W, padx=20, pady=15)
        
        desc_label = tk.Label(
            title_frame, 
            text="基于FFmpeg实现高质量视频转换，支持多种视频格式",
            font=("微软雅黑", 11),
            bg="#34495e",
            fg="#bdc3c7"
        )
        desc_label.pack(anchor=tk.W, padx=20, pady=0, ipady=5)
        
        # 主容器
        main_frame = tk.Frame(self.root, bg="#ffffff", bd=0)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 已选文件区域 - 左侧
        files_frame = tk.LabelFrame(main_frame, text="已选择文件", font=("微软雅黑", 12, "bold"), bg="#ffffff", fg="#34495e", bd=1, relief=tk.GROOVE)
        files_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=5, side=tk.TOP)
        
        # 文件列表
        files_inner_frame = tk.Frame(files_frame, bg="#ffffff")
        files_inner_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 文件列表与滚动条
        list_scrollbar = tk.Scrollbar(files_inner_frame, bg="#ecf0f1")
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.file_list = tk.Listbox(
            files_inner_frame, 
            font=("微软雅黑", 10),
            bg="#f8f9fa",
            fg="#2c3e50",
            bd=1,
            relief=tk.SOLID,
            selectmode=tk.MULTIPLE,
            height=6,  # 减小高度，适配小窗口
            yscrollcommand=list_scrollbar.set
        )
        self.file_list.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        list_scrollbar.config(command=self.file_list.yview)
        
        # 文件操作按钮
        file_buttons_frame = tk.Frame(files_frame, bg="#ffffff")
        file_buttons_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 添加文件按钮
        add_file_btn = tk.Button(
            file_buttons_frame, 
            text="添加文件", 
            command=self.add_files, 
            font=("微软雅黑", 11, "bold"),
            bg="#3498db",
            fg="white",
            bd=1, 
            relief=tk.RAISED,
            padx=15,
            pady=6, 
            width=12
        )
        add_file_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 添加文件夹按钮
        add_folder_btn = tk.Button(
            file_buttons_frame, 
            text="添加文件夹", 
            command=self.add_folder, 
            font=("微软雅黑", 11, "bold"),
            bg="#2ecc71",
            fg="white",
            bd=1, 
            relief=tk.RAISED,
            padx=15,
            pady=6, 
            width=12
        )
        add_folder_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 移除所选按钮
        remove_selected_btn = tk.Button(
            file_buttons_frame, 
            text="移除所选", 
            command=self.remove_selected, 
            font=("微软雅黑", 11, "bold"),
            bg="#e74c3c",
            fg="white",
            bd=1, 
            relief=tk.RAISED,
            padx=15,
            pady=6, 
            width=12
        )
        remove_selected_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 清空所有按钮
        clear_all_btn = tk.Button(
            file_buttons_frame, 
            text="清空所有", 
            command=self.clear_all, 
            font=("微软雅黑", 11, "bold"),
            bg="#f39c12",
            fg="white",
            bd=1, 
            relief=tk.RAISED,
            padx=15,
            pady=6, 
            width=12
        )
        clear_all_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 右侧设置区域
        settings_frame = tk.Frame(main_frame, bg="#ffffff")
        settings_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=5, side=tk.TOP)
        
        # 输出设置区域
        output_frame = tk.LabelFrame(settings_frame, text="输出设置", font=("微软雅黑", 12, "bold"), bg="#ffffff", fg="#34495e", bd=1, relief=tk.GROOVE)
        output_frame.pack(fill=tk.X, pady=5, side=tk.TOP)
        
        # 输出目录
        output_dir_frame = tk.Frame(output_frame, bg="#ffffff")
        output_dir_frame.pack(fill=tk.X, padx=15, pady=10, side=tk.TOP)
        
        dir_label = tk.Label(
            output_dir_frame, 
            text="输出目录:", 
            font=("微软雅黑", 11, "bold"),
            bg="#ffffff",
            fg="#34495e",
            width=10, 
            anchor=tk.W
        )
        dir_label.pack(side=tk.LEFT, anchor=tk.CENTER, padx=5)
        
        self.output_dir_entry = tk.Entry(
            output_dir_frame, 
            font=("微软雅黑", 10),
            bd=1, 
            relief=tk.SOLID,
            bg="#f8f9fa",
            fg="#2c3e50"
        )
        self.output_dir_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True, anchor=tk.CENTER)
        
        # 设置默认输出目录
        output_dir = os.path.join(os.getcwd(), "output")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        self.output_dir_entry.insert(0, output_dir)
        
        # 修改输出目录按钮
        modify_dir_btn = tk.Button(
            output_dir_frame, 
            text="浏览", 
            command=self.browse_output_dir, 
            font=("微软雅黑", 10, "bold"),
            bg="#3498db",
            fg="white",
            bd=1, 
            relief=tk.RAISED,
            padx=12,
            pady=3, 
            width=8
        )
        modify_dir_btn.pack(side=tk.RIGHT, anchor=tk.CENTER, padx=5)
        
        # 输出格式
        format_frame = tk.LabelFrame(output_frame, text="输出格式", font=("微软雅黑", 11, "bold"), bg="#f8f9fa", fg="#34495e", bd=1, relief=tk.SUNKEN)
        format_frame.pack(fill=tk.X, padx=15, pady=10, side=tk.TOP)
        
        # 常用格式按钮
        self.format_var = tk.StringVar(value="mp4")
        formats = [
            ("MP4", "mp4"), ("MKV", "mkv"), ("AVI", "avi"), 
            ("WMV", "wmv"), ("MOV", "mov"), ("FLV", "flv"),
            ("MPEG", "mpeg"), ("3GP", "3gp")
        ]
        
        # 格式按钮网格
        format_grid_frame = tk.Frame(format_frame, bg="#f8f9fa")
        format_grid_frame.pack(fill=tk.X, padx=10, pady=10)
        
        for i, (name, value) in enumerate(formats):
            btn = tk.Radiobutton(
                format_grid_frame,
                text=name,
                variable=self.format_var,
                value=value,
                font=("微软雅黑", 10),
                bg="#f8f9fa",
                fg="#2c3e50",
                activebackground="#f8f9fa",
                activeforeground="#3498db",
                selectcolor="#e3f2fd",
                padx=10,
                pady=3
            )
            btn.grid(row=i//4, column=i%4, padx=15, pady=5, sticky=tk.W)
        
        # 高级设置
        advanced_frame = tk.LabelFrame(settings_frame, text="高级设置", font=("微软雅黑", 12, "bold"), bg="#ffffff", fg="#34495e", bd=1, relief=tk.GROOVE)
        advanced_frame.pack(fill=tk.X, pady=5, side=tk.TOP)
        
        # 高级设置网格
        advanced_grid_frame = tk.Frame(advanced_frame, bg="#ffffff")
        advanced_grid_frame.pack(fill=tk.X, padx=15, pady=10)
        
        # 分辨率设置
        resolution_label = tk.Label(
            advanced_grid_frame, 
            text="分辨率:", 
            font=(
            "微软雅黑", 11, "bold"),
            bg="#ffffff",
            fg="#34495e",
            width=12, 
            anchor=tk.W
        )
        resolution_label.grid(row=0, column=0, sticky=tk.W, padx=10, pady=8)
        
        self.resolution_var = tk.StringVar(value="原始分辨率")
        resolutions = [
            "原始分辨率",
            "4K (3840x2160)",
            "2K (2560x1440)",
            "1080p (1920x1080)",
            "1080p竖屏 (1080x1920)",
            "720p (1280x720)",
            "720p竖屏 (720x1280)",
            "480p (854x480)",
            "480p竖屏 (480x854)",
            "360p (640x360)",
            "360p竖屏 (360x640)"
        ]
        resolution_combo = ttk.Combobox(
            advanced_grid_frame, 
            textvariable=self.resolution_var, 
            values=resolutions, 
            state="readonly", 
            font=(
            "微软雅黑", 10),
            width=25
        )
        resolution_combo.grid(row=0, column=1, padx=10, pady=8, sticky=tk.W)
        
        # 码率设置
        bitrate_label = tk.Label(
            advanced_grid_frame, 
            text="视频码率:", 
            font=(
            "微软雅黑", 11, "bold"),
            bg="#ffffff",
            fg="#34495e",
            width=12, 
            anchor=tk.W
        )
        bitrate_label.grid(row=1, column=0, sticky=tk.W, padx=10, pady=8)
        
        self.bitrate_var = tk.StringVar(value="自动")
        bitrates = [
            "自动",
            "50 Mbps",
            "40 Mbps",
            "30 Mbps",
            "20 Mbps",
            "10 Mbps",
            "5 Mbps"
        ]
        bitrate_combo = ttk.Combobox(
            advanced_grid_frame, 
            textvariable=self.bitrate_var, 
            values=bitrates, 
            state="readonly", 
            font=(
            "微软雅黑", 10),
            width=25
        )
        bitrate_combo.grid(row=1, column=1, padx=10, pady=8, sticky=tk.W)
        
        # 检测系统GPU
        detected_gpus = self.detect_gpus()
        
        # 检测NVIDIA显卡
        has_nvidia = any('nvidia' in gpu.lower() for gpu in detected_gpus)
        # 检测AMD显卡
        has_amd = any('amd' in gpu.lower() or 'radeon' in gpu.lower() for gpu in detected_gpus)
        # 检测Intel显卡
        has_intel = any('intel' in gpu.lower() or 'hd graphics' in gpu.lower() or 'iris' in gpu.lower() for gpu in detected_gpus)
        
        # GPU加速选项
        gpu_label = tk.Label(
            advanced_grid_frame, 
            text="GPU加速:", 
            font=(
            "微软雅黑", 11, "bold"),
            bg="#ffffff",
            fg="#34495e",
            width=12, 
            anchor=tk.W
        )
        gpu_label.grid(row=2, column=0, sticky=tk.W, padx=10, pady=8)
        
        # 根据检测到的GPU类型生成可用的加速选项
        gpu_options = []
        default_gpu_accel = ""
        
        if has_nvidia:
            # 只显示NVIDIA CUDA选项
            gpu_options = ["NVIDIA CUDA"]
            default_gpu_accel = "NVIDIA CUDA"
        elif has_amd:
            # 只显示AMD VCE选项
            gpu_options = ["AMD VCE"]
            default_gpu_accel = "AMD VCE"
        elif has_intel:
            # 只显示Intel QSV选项
            gpu_options = ["Intel QSV"]
            default_gpu_accel = "Intel QSV"
        else:
            # 没有检测到显卡，使用CPU
            gpu_options = ["CPU编码"]
            default_gpu_accel = "CPU编码"
        
        self.gpu_accel_var = tk.StringVar(value=default_gpu_accel)
        gpu_combo = ttk.Combobox(
            advanced_grid_frame, 
            textvariable=self.gpu_accel_var, 
            values=gpu_options, 
            state="readonly", 
            font=(
            "微软雅黑", 10),
            width=25
        )
        gpu_combo.grid(row=2, column=1, padx=10, pady=8, sticky=tk.W)
        
        # 转换控制区域 - 底部
        control_frame = tk.LabelFrame(settings_frame, text="转换控制", font=("微软雅黑", 12, "bold"), bg="#ffffff", fg="#34495e", bd=1, relief=tk.GROOVE)
        control_frame.pack(fill=tk.X, pady=5, side=tk.TOP)
        
        # 控制按钮
        control_buttons_frame = tk.Frame(control_frame, bg="#ffffff")
        control_buttons_frame.pack(fill=tk.X, padx=20, pady=15)
        
        # 开始转换按钮
        self.convert_btn = tk.Button(
            control_buttons_frame, 
            text="开始转换", 
            command=self.start_conversion, 
            font=("微软雅黑", 14, "bold"),
            bg="#2ecc71",
            fg="white",
            bd=1, 
            relief=tk.RAISED,
            padx=20,
            pady=10,
            activebackground="#27ae60"
        )
        self.convert_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # 停止转换按钮
        self.stop_btn = tk.Button(
            control_buttons_frame, 
            text="停止转换", 
            command=self.stop_conversion, 
            font=("微软雅黑", 14, "bold"),
            bg="#e74c3c",
            fg="white",
            bd=1, 
            relief=tk.RAISED,
            padx=20,
            pady=10,
            state=tk.DISABLED,  # 初始状态不可用
            activebackground="#c0392b"
        )
        self.stop_btn.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)
        
        # 选项设置
        options_frame = tk.Frame(control_frame, bg="#ffffff")
        options_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # 自动打开输出目录选项
        self.open_dir_var = tk.BooleanVar(value=True)
        open_dir_checkbox = tk.Checkbutton(
            options_frame, 
            text="转换完成后自动打开输出目录", 
            variable=self.open_dir_var,
            font=("微软雅黑", 11),
            bg="#ffffff",
            fg="#34495e",
            activebackground="#ffffff",
            activeforeground="#34495e"
        )
        open_dir_checkbox.pack(side=tk.LEFT, anchor=tk.W)
        
        # 进度条和状态区域
        progress_status_frame = tk.Frame(control_frame, bg="#ffffff")
        progress_status_frame.pack(fill=tk.X, padx=20, pady=15)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_status_frame, 
            variable=self.progress_var, 
            maximum=100,
            length=400,
            style="TProgressbar"
        )
        self.progress_bar.pack(fill=tk.X, expand=True, pady=10)
        
        # 状态标签
        self.status_var = tk.StringVar(value="就绪")
        status_label = tk.Label(
            progress_status_frame, 
            textvariable=self.status_var, 
            font=("微软雅黑", 12, "bold"),
            bg="#ffffff",
            fg="#2ecc71"
        )
        status_label.pack(pady=5)
        
        # 日志区域
        log_frame = tk.LabelFrame(settings_frame, text="转换日志", font=("微软雅黑", 12, "bold"), bg="#ffffff", fg="#34495e", bd=1, relief=tk.GROOVE)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5, side=tk.TOP)
        
        log_inner_frame = tk.Frame(log_frame, bg="#ffffff")
        log_inner_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 日志文本框与滚动条
        log_scrollbar = tk.Scrollbar(log_inner_frame, bg="#ecf0f1")
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text = tk.Text(
            log_inner_frame, 
            height=5,  # 减小初始高度，适配小窗口
            font=(
            "Consolas", 10),
            bg="#f8f9fa",
            fg="#2c3e50",
            bd=1,
            relief=tk.SOLID,
            wrap=tk.WORD,
            yscrollcommand=log_scrollbar.set
        )
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.config(command=self.log_text.yview)
        
        # 显示检测到的GPU信息
        detected_gpus = self.detect_gpus()
        optimal_gpu_accel = self.get_optimal_gpu_accel()
        
        if detected_gpus:
            detected_gpus_str = ", ".join(detected_gpus)
            self.log_text.insert(tk.END, f"检测到显卡: {detected_gpus_str}\n")
            self.log_text.insert(tk.END, f"自动选择GPU加速: {optimal_gpu_accel}\n\n")
        else:
            self.log_text.insert(tk.END, "未检测到可用显卡，默认使用CPU编码\n\n")
        self.log_text.see(tk.END)
        
        # 配置ttk样式
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TProgressbar", 
                        thickness=18,
                        troughcolor='#ecf0f1',
                        background='#3498db',
                        borderwidth=0)
        style.configure("TCombobox", 
                        fieldbackground='#f8f9fa',
                        background='#3498db',
                        arrowcolor='#3498db',
                        bordercolor='#bdc3c7',
                        focuscolor='#3498db')
        style.map("TCombobox", 
                  fieldbackground=[('readonly', '#f8f9fa')],
                  background=[('readonly', '#3498db')])
        
        # 初始化转换进程变量
        self.conversion_process = None
    
    def add_files(self):
        """添加多个视频文件"""
        file_paths = filedialog.askopenfilenames(
            filetypes=[("视频文件", "*.mp4;*.mkv;*.avi;*.wmv;*.mov;*.flv;*.webm;*.mpg;*.mpeg;*.3gp")]
        )
        if file_paths:
            for file_path in file_paths:
                self.file_list.insert(tk.END, file_path)
    
    def add_folder(self):
        """添加文件夹中的所有视频文件"""
        folder_path = filedialog.askdirectory()
        if folder_path:
            for root, _, files in os.walk(folder_path):
                for file in files:
                    if any(file.lower().endswith(ext) for ext in ['.mp4', '.mkv', '.avi', '.wmv', '.mov', '.flv', '.webm', '.mpg', '.mpeg', '.3gp']):
                        file_path = os.path.join(root, file)
                        self.file_list.insert(tk.END, file_path)
    
    def remove_selected(self):
        """移除选中的文件"""
        selected_indices = self.file_list.curselection()[::-1]  # 从后往前删除
        for index in selected_indices:
            self.file_list.delete(index)
    
    def clear_all(self):
        """清空所有文件"""
        self.file_list.delete(0, tk.END)
    
    def browse_output_dir(self):
        """浏览选择输出目录"""
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.output_dir_entry.delete(0, tk.END)
            self.output_dir_entry.insert(0, dir_path)
    
    def start_conversion(self):
        """开始转换视频"""
        import threading
        import time
        
        try:
            # 验证输入
            file_paths = list(self.file_list.get(0, tk.END))
            output_dir = self.output_dir_entry.get().strip()
            output_format = self.format_var.get().lower()
            
            if not file_paths:
                messagebox.showinfo("提示", "未检测到待转换文件，请先点击添加文件按钮选择需要转换的文件")
                return
            
            if not os.path.exists(output_dir):
                messagebox.showerror("错误", "输出目录不存在")
                return
            
            # 使用默认高质量参数
            quality_params = self.quality_params
            
            # 解析分辨率参数
            resolution = self.resolution_var.get()
            resolution_param = ""
            if resolution != "原始分辨率":
                # 提取分辨率值，如"1920x1080"
                res_value = resolution.split(" (")[1].rstrip(")")
                resolution_param = f"-s {res_value}"
            
            # 解析码率参数
            bitrate = self.bitrate_var.get()
            bitrate_param = ""
            
            if bitrate != "自动":
                # 移除空格，如"10Mbps"
                bitrate_value = bitrate.replace(" ", "")
                # 转换为FFmpeg期望的格式，如"10Mbps" -> "10M"，"800Kbps" -> "800K"
                if bitrate_value.endswith("Mbps"):
                    bitrate_value = bitrate_value[:-4] + "M"
                elif bitrate_value.endswith("Kbps"):
                    bitrate_value = bitrate_value[:-4] + "K"
                bitrate_param = f"-b:v {bitrate_value}"
            
            # 解析GPU加速参数
            gpu_accel = self.gpu_accel_var.get()
            gpu_param = ""
            
            # 根据选择的GPU加速类型设置相应的编码器
            if gpu_accel == "NVIDIA CUDA":
                gpu_param = "-vcodec h264_nvenc"
            elif gpu_accel == "AMD VCE":
                gpu_param = "-vcodec h264_amf"
            elif gpu_accel == "Intel QSV":
                gpu_param = "-vcodec h264_qsv"
            else:  # CPU编码或其他选项
                gpu_param = ""  # 使用默认的CPU编码器
            
            # 更新UI状态
            self.log_text.delete(1.0, tk.END)
            self.log_text.insert(tk.END, "开始转换按钮被点击...\n")
            self.log_text.insert(tk.END, f"总共要转换 {len(file_paths)} 个文件\n\n")
            self.status_var.set("转换中...")
            self.progress_var.set(0)
            
            # 禁用开始按钮，启用停止按钮
            self.convert_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            
            # 初始化转换进程变量
            self.conversion_process = None
            self.done_flag = False
            self.current_file_index = 0
            
            # 立即显示一些信息
            self.log_text.insert(tk.END, "初始化转换参数...\n")
            self.log_text.insert(tk.END, f"输出格式: {output_format}\n")
            self.log_text.insert(tk.END, f"质量设置: 高质量\n")
            self.log_text.insert(tk.END, f"分辨率: {resolution}\n")
            self.log_text.insert(tk.END, f"视频码率: {bitrate}\n")
            self.log_text.insert(tk.END, f"输出目录: {output_dir}\n\n")
            self.log_text.see(tk.END)
            self.root.update()
            
            # 定义转换线程函数
            def conversion_thread():
                """转换线程函数"""
                nonlocal file_paths, output_dir, output_format, quality_params, resolution_param, bitrate_param, gpu_param
                
                # 记录当前正在转换的输出文件，用于停止时删除不完整文件
                current_output_file = None
                
                try:
                    total_files = len(file_paths)
                    for i, input_file in enumerate(file_paths):
                        if self.done_flag:
                            # 转换被停止
                            break
                            
                        self.current_file_index = i + 1
                        
                        # 更新状态为当前正在转换的文件
                        self.root.after(0, lambda f=input_file, idx=i+1: self.log_text.insert(tk.END, f"=== 开始转换第 {idx}/{total_files} 个文件: {f} ===\n"))
                        self.root.after(0, lambda: self.log_text.see(tk.END))
                        self.root.after(0, lambda: self.root.update())
                        
                        # 生成输出文件名
                        input_filename = os.path.basename(input_file)
                        input_name, _ = os.path.splitext(input_filename)
                        current_output_file = os.path.join(output_dir, f"{input_name}_converted.{output_format}")
                        
                        # 确保输出目录存在
                        os.makedirs(output_dir, exist_ok=True)
                        
                        # 检查输出目录权限
                        try:
                            test_file = os.path.join(output_dir, ".test_write.txt")
                            with open(test_file, 'w') as f:
                                f.write("test")
                            os.remove(test_file)
                            self.root.after(0, lambda: self.log_text.insert(tk.END, f"✓ 输出目录写入权限检查通过\n"))
                        except Exception as e:
                            self.root.after(0, lambda: self.log_text.insert(tk.END, f"⚠ 输出目录写入权限检查失败: {str(e)}\n"))
                            self.root.after(0, lambda: self.log_text.see(tk.END))
                            self.root.after(0, lambda: self.root.update())
                        
                        # 检查输入文件是否可读取
                        try:
                            with open(input_file, 'rb') as f:
                                f.read(100)  # 读取前100字节测试
                            self.root.after(0, lambda: self.log_text.insert(tk.END, f"✓ 输入文件读取权限检查通过\n"))
                        except Exception as e:
                            self.root.after(0, lambda: self.log_text.insert(tk.END, f"⚠ 输入文件读取权限检查失败: {str(e)}\n"))
                            self.root.after(0, lambda: self.log_text.see(tk.END))
                            self.root.after(0, lambda: self.root.update())
                        
                        # 构建FFmpeg命令
                        cmd = [
                            self.ffmpeg_path,
                            "-i", input_file,
                            "-y",  # 覆盖输出文件
                        ]
                        
                        # 添加CPU/GPU编码参数
                        if gpu_param:
                            # GPU编码
                            gpu_args = gpu_param.split()
                            cmd.extend(gpu_args)
                            # 添加音频编码参数（GPU编码时需要明确指定）
                            cmd.extend(["-acodec", "aac"])
                        else:
                            # 默认使用CPU编码
                            cmd.extend(["-vcodec", "libx264", "-acodec", "aac"])
                        
                        # 添加分辨率参数
                        if resolution_param:
                            resolution_args = resolution_param.split()
                            cmd.extend(resolution_args)
                        
                        # 添加码率参数
                        if bitrate_param:
                            bitrate_args = bitrate_param.split()
                            cmd.extend(bitrate_args)
                        
                        # 添加质量参数 - 确保正确分割参数
                        quality_args = quality_params.split()
                        cmd.extend(quality_args)
                        
                        # 添加输出文件
                        cmd.append(current_output_file)
                        
                        # 显示执行的命令
                        cmd_str = ' '.join(cmd)
                        self.root.after(0, lambda: self.log_text.insert(tk.END, f"执行FFmpeg命令: {cmd_str}\n"))
                        self.root.after(0, lambda: self.log_text.insert(tk.END, f"输入文件: {input_file}\n"))
                        self.root.after(0, lambda: self.log_text.insert(tk.END, f"输出文件: {current_output_file}\n"))
                        self.root.after(0, lambda: self.log_text.see(tk.END))
                        self.root.after(0, lambda: self.root.update())
                        
                        # 执行FFmpeg命令，禁用缓冲并隐藏命令窗口
                        startupinfo = None
                        creationflags = 0
                        if sys.platform == 'win32':
                            startupinfo = subprocess.STARTUPINFO()
                            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                            creationflags = subprocess.CREATE_NO_WINDOW
                        
                        # 执行策略：优先使用直接执行，失败后尝试shell=True
                        process = None
                        execution_attempts = []
                        
                        # 尝试1：直接执行（推荐方式）
                        try:
                            self.root.after(0, lambda: self.log_text.insert(tk.END, "尝试1：直接执行FFmpeg命令\n"))
                            self.root.after(0, lambda: self.log_text.see(tk.END))
                            self.root.after(0, lambda: self.root.update())
                            
                            process = subprocess.Popen(
                                cmd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                text=True,
                                encoding='utf-8',
                                bufsize=0,  # 禁用缓冲
                                startupinfo=startupinfo,
                                creationflags=creationflags
                            )
                            execution_attempts.append("直接执行成功")
                        except Exception as e:
                            execution_attempts.append(f"直接执行失败: {str(e)}")
                            
                            # 尝试2：使用shell=True（Windows特殊情况）
                            try:
                                self.root.after(0, lambda: self.log_text.insert(tk.END, f"尝试2：使用shell=True执行FFmpeg命令\n"))
                                self.root.after(0, lambda: self.log_text.see(tk.END))
                                self.root.after(0, lambda: self.root.update())
                                
                                # 对于Windows，确保路径使用双引号包裹
                                if sys.platform == 'win32':
                                    # 构建基础命令
                                    cmd_str = f'"{self.ffmpeg_path}" -i "{input_file}" -y '
                                    
                                    # 添加编码参数
                                    if gpu_param:
                                        cmd_str += f'{gpu_param} -acodec aac '
                                    else:
                                        cmd_str += '-vcodec libx264 -acodec aac '
                                    
                                    # 添加分辨率参数
                                    if resolution_param:
                                        cmd_str += f"{resolution_param} "
                                    
                                    # 添加码率参数
                                    if bitrate_param:
                                        cmd_str += f"{bitrate_param} "
                                    
                                    # 添加质量参数
                                    cmd_str += f"{quality_params} "
                                    
                                    # 添加输出文件
                                    cmd_str += f'"{current_output_file}"'
                                
                                process = subprocess.Popen(
                                    cmd_str,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT,
                                    text=True,
                                    encoding='utf-8',
                                    bufsize=0,  # 禁用缓冲
                                    startupinfo=startupinfo,
                                    creationflags=creationflags,
                                    shell=True
                                )
                                execution_attempts.append("shell=True执行成功")
                            except Exception as e2:
                                execution_attempts.append(f"shell=True执行失败: {str(e2)}")
                                
                                # 尝试3：简化命令，只进行格式转换，不修改编码
                                try:
                                    self.root.after(0, lambda: self.log_text.insert(tk.END, "尝试3：使用简化命令执行FFmpeg（仅格式转换）\n"))
                                    self.root.after(0, lambda: self.log_text.see(tk.END))
                                    self.root.after(0, lambda: self.root.update())
                                    
                                    simple_cmd = [
                                        self.ffmpeg_path,
                                        "-i", input_file,
                                        "-y",
                                        "-c", "copy"  # 直接复制流，不重新编码
                                    ]
                                    simple_cmd.append(current_output_file)
                                    
                                    process = subprocess.Popen(
                                        simple_cmd,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT,
                                        text=True,
                                        encoding='utf-8',
                                        bufsize=0,
                                        startupinfo=startupinfo,
                                        creationflags=creationflags
                                    )
                                    execution_attempts.append("简化命令执行成功")
                                except Exception as e3:
                                    execution_attempts.append(f"简化命令执行失败: {str(e3)}")
                                    
                                    # 所有尝试都失败，记录错误
                                    self.root.after(0, lambda: self.log_text.insert(tk.END, f"所有执行尝试都失败: {'; '.join(execution_attempts)}\n"))
                                    self.root.after(0, lambda: self.log_text.see(tk.END))
                                    self.root.after(0, lambda: self.root.update())
                                    continue
                        
                        # 检查process是否成功创建
                        if process is None:
                            self.root.after(0, lambda: self.log_text.insert(tk.END, f"第 {i+1}/{total_files} 个文件转换失败：无法创建FFmpeg进程\n\n"))
                            self.root.after(0, lambda: self.log_text.see(tk.END))
                            self.root.after(0, lambda: self.root.update())
                            continue
                        
                        # 更新进程引用
                        self.conversion_process = process
                        
                        # 显示进程已启动
                        self.root.after(0, lambda: self.log_text.insert(tk.END, "FFmpeg进程已启动...\n"))
                        self.root.after(0, lambda: self.log_text.see(tk.END))
                        self.root.after(0, lambda: self.root.update())
                        
                        # 读取输出
                        duration = 0
                        current_time = 0
                        line_count = 0
                        
                        # 循环读取输出
                        while True:
                            if self.done_flag:
                                break
                            
                            # 读取一行输出
                            try:
                                line = process.stdout.readline()
                            except Exception as e:
                                self.root.after(0, lambda: self.log_text.insert(tk.END, f"读取进程输出时出错: {str(e)}\n"))
                                self.root.after(0, lambda: self.log_text.see(tk.END))
                                self.root.after(0, lambda: self.root.update())
                                break
                            
                            if not line:
                                if process.poll() is not None:
                                    break
                                time.sleep(0.01)
                                continue
                            
                            line_count += 1
                            
                            # 在主线程中更新日志
                            def update_log():
                                self.log_text.insert(tk.END, line)
                                self.log_text.see(tk.END)
                            self.root.after(0, update_log)
                            
                            # 解析总时长
                            if "Duration:" in line and duration == 0:
                                try:
                                    duration_str = line.split("Duration:")[1].split(",")[0].strip()
                                    h, m, s = duration_str.split(":")
                                    duration = float(h) * 3600 + float(m) * 60 + float(s)
                                    def update_duration():
                                        self.log_text.insert(tk.END, f"\n解析到总时长: {duration:.2f} 秒\n")
                                        self.log_text.see(tk.END)
                                    self.root.after(0, update_duration)
                                except Exception as e:
                                    self.root.after(0, lambda: self.log_text.insert(tk.END, f"解析时长时出错: {str(e)}\n"))
                                    self.root.after(0, lambda: self.log_text.see(tk.END))
                                    self.root.after(0, lambda: self.root.update())
                            
                            # 解析当前进度
                            if "time=" in line and duration > 0:
                                try:
                                    time_str = line.split("time=")[1].split()[0]
                                    h, m, s = time_str.split(":")
                                    current_time = float(h) * 3600 + float(m) * 60 + float(s)
                                    file_progress = (current_time / duration) * 100
                                    # 计算整体进度
                                    overall_progress = ((i * 100) + file_progress) / total_files
                                    def update_progress():
                                        self.progress_var.set(min(overall_progress, 100))
                                        if line_count % 10 == 0:
                                            self.log_text.insert(tk.END, f"当前文件进度: {file_progress:.1f}% | 整体进度: {overall_progress:.1f}%\n")
                                            self.log_text.see(tk.END)
                                    self.root.after(0, update_progress)
                                except Exception as e:
                                    self.root.after(0, lambda: self.log_text.insert(tk.END, f"解析进度时出错: {str(e)}\n"))
                                    self.root.after(0, lambda: self.log_text.see(tk.END))
                                    self.root.after(0, lambda: self.root.update())
                            
                            # 定期更新UI
                            if line_count % 5 == 0:
                                def refresh_ui():
                                    self.root.update()
                                self.root.after(0, refresh_ui)
                        
                        # 等待进程结束
                        try:
                            return_code = process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            self.root.after(0, lambda: self.log_text.insert(tk.END, "FFmpeg进程超时，强制终止\n"))
                            self.root.after(0, lambda: self.log_text.see(tk.END))
                            self.root.after(0, lambda: self.root.update())
                            try:
                                process.terminate()
                                process.wait(timeout=2)
                            except:
                                try:
                                    process.kill()
                                    process.wait(timeout=1)
                                except:
                                    pass
                            return_code = -1  # 超时返回码
                        
                        # 显示返回码
                        def show_return_code():
                            self.log_text.insert(tk.END, f"FFmpeg返回码: {return_code}\n")
                            self.log_text.see(tk.END)
                            
                            if return_code == 0:
                                self.log_text.insert(tk.END, f"第 {i+1}/{total_files} 个文件转换完成！\n\n")
                            else:
                                self.log_text.insert(tk.END, f"第 {i+1}/{total_files} 个文件转换失败！返回码: {return_code}\n\n")
                            
                            self.log_text.see(tk.END)
                            self.root.update()
                        
                        self.root.after(0, show_return_code)
                    
                    # 删除不完整的输出文件（如果转换被停止）
                    if self.done_flag and current_output_file and os.path.exists(current_output_file):
                        try:
                            os.remove(current_output_file)
                            self.root.after(0, lambda: self.log_text.insert(tk.END, f"已删除不完整的输出文件: {os.path.basename(current_output_file)}\n"))
                            self.root.after(0, lambda: self.log_text.see(tk.END))
                        except Exception as e:
                            self.root.after(0, lambda: self.log_text.insert(tk.END, f"删除不完整文件失败: {str(e)}\n"))
                            self.root.after(0, lambda: self.log_text.see(tk.END))
                    
                    # 所有文件转换完成或被停止
                    def show_final_result():
                        if self.done_flag:
                            self.log_text.insert(tk.END, "转换已被停止！\n")
                            self.status_var.set("转换已停止")
                            self.progress_var.set(0)
                            messagebox.showinfo("提示", "转换已被停止")
                        else:
                            self.log_text.insert(tk.END, "=== 所有文件转换完成！ ===\n")
                            self.status_var.set("转换完成")
                            self.progress_var.set(100)
                            messagebox.showinfo("成功", f"所有 {total_files} 个文件转换完成！\n输出目录: {output_dir}")
                            
                            # 自动打开输出目录
                            if self.open_dir_var.get():
                                try:
                                    self.log_text.insert(tk.END, f"正在打开输出目录: {output_dir}\n")
                                    self.log_text.see(tk.END)
                                    self.root.update()
                                    
                                    # 仅支持Windows系统打开目录
                                    if sys.platform == 'win32':
                                        os.startfile(output_dir)
                                        self.log_text.insert(tk.END, "输出目录已打开\n")
                                    else:
                                        self.log_text.insert(tk.END, "当前系统不支持自动打开目录\n")
                                except Exception as e:
                                    self.log_text.insert(tk.END, f"打开输出目录失败: {str(e)}\n")
                        
                        # 恢复按钮状态
                        self.convert_btn.config(state=tk.NORMAL)
                        self.stop_btn.config(state=tk.DISABLED)
                        
                        self.log_text.see(tk.END)
                        self.root.update()
                    
                    self.root.after(0, show_final_result)
                    
                except Exception as e:
                    import traceback
                    error_msg = f"\n转换出错: {str(e)}\n"
                    error_msg += f"详细信息: {traceback.format_exc()}\n"
                    
                    def show_error():
                        self.log_text.insert(tk.END, error_msg)
                        self.log_text.see(tk.END)
                        self.status_var.set("转换失败")
                        self.progress_var.set(0)
                        self.convert_btn.config(state=tk.NORMAL)
                        self.stop_btn.config(state=tk.DISABLED)
                        messagebox.showerror("错误", f"转换出错: {str(e)}")
                        self.root.update()
                    
                    self.root.after(0, show_error)
                finally:
                    self.conversion_process = None
                    self.done_flag = False
            
            # 启动转换线程
            self.conversion_thread = threading.Thread(target=conversion_thread, daemon=True)
            self.conversion_thread.start()
            
        except Exception as e:
            # 处理主线程中的异常
            import traceback
            error_msg = f"\n主线程出错: {str(e)}\n"
            error_msg += f"详细信息: {traceback.format_exc()}\n"
            
            self.log_text.insert(tk.END, error_msg)
            self.log_text.see(tk.END)
            self.status_var.set("转换失败")
            self.progress_var.set(0)
            self.convert_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.log_text.see(tk.END)
            self.root.update()
            messagebox.showerror("错误", f"转换出错: {str(e)}")
    
    def stop_conversion(self):
        """停止正在进行的转换"""
        # 安全停止，忽略所有异常
        try:
            # 检查转换进程是否存在
            if hasattr(self, 'conversion_process') and self.conversion_process is not None:
                self.status_var.set("正在停止...")
                self.root.update()
                
                # 设置完成标志，通知转换线程停止
                if hasattr(self, 'done_flag'):
                    self.done_flag = True
                
                # 记录当前进程
                process = self.conversion_process
                self.conversion_process = None
                
                # 尝试终止进程
                try:
                    process.terminate()
                    
                    # 等待进程结束
                    try:
                        process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        # 超时后强制终止
                        try:
                            process.kill()
                            process.wait(timeout=1)
                        except:
                            pass
                except:
                    pass
                
                # 更新UI
                self.log_text.insert(tk.END, "\n转换已被停止！\n")
                self.status_var.set("转换已停止")
                self.progress_var.set(0)
                
            # 恢复按钮状态
            self.convert_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            
            self.log_text.see(tk.END)
            self.root.update()
            
        except Exception as e:
            # 忽略所有停止过程中的异常
            try:
                self.log_text.insert(tk.END, "\n转换已被停止！\n")
                self.status_var.set("转换已停止")
                self.progress_var.set(0)
                self.convert_btn.config(state=tk.NORMAL)
                self.stop_btn.config(state=tk.DISABLED)
                # 确保done_flag为True，避免转换线程显示成功
                if hasattr(self, 'done_flag'):
                    self.done_flag = True
                self.log_text.see(tk.END)
                self.root.update()
            except:
                pass

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoConverter(root)
    root.mainloop()