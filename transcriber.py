import customtkinter as ctk
import threading
import os
import time
from tkinter import filedialog, messagebox
from faster_whisper import WhisperModel
from opencc import OpenCC
from datetime import timedelta
import re
import platform
# --- 設定 ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class TranscriberApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 視窗設定
        self.title("MP3 轉繁體中文字幕 (Whisper + OpenCC)")
        self.geometry("750x650")
        
        # 變數
        self.file_paths = []  # 改為陣列以支援批次處理
        self.is_running = False
        self.cancel_flag = False  # 取消標記
        self.current_file_index = 0
        self.start_time = None
        
        # 初始化繁簡轉換器
        self.cc = OpenCC('s2twp')
        self.model = None  # 保存模型以便重用

        # 建立 UI
        self.create_widgets()

    def create_widgets(self):
        # 標題
        self.header_label = ctk.CTkLabel(self, text="MP3 語音轉繁體中文工具", font=("Arial Bold", 22))
        self.header_label.pack(pady=15)

        # 檔案選擇區
        self.file_frame = ctk.CTkFrame(self)
        self.file_frame.pack(pady=10, padx=20, fill="x")
        
        # 單檔選擇按鈕
        self.select_btn = ctk.CTkButton(
            self.file_frame, 
            text="選擇單一檔案", 
            command=self.select_file, 
            width=130
        )
        self.select_btn.pack(side="left", padx=10, pady=15)
        
        # 批次選擇按鈕
        self.batch_btn = ctk.CTkButton(
            self.file_frame, 
            text="批次選擇", 
            command=self.select_batch_files,
            width=130,
            fg_color="#1f538d"
        )
        self.batch_btn.pack(side="left", padx=10, pady=15)
        
        # 檔案標籤
        self.file_label = ctk.CTkLabel(self.file_frame, text="尚未選擇檔案", text_color="gray")
        self.file_label.pack(side="left", padx=10)

        # 設定區
        self.settings_frame = ctk.CTkFrame(self)
        self.settings_frame.pack(pady=10, padx=20, fill="x")
        
        # 模型大小選擇
        ctk.CTkLabel(self.settings_frame, text="準確度模型 (Model):").pack(side="left", padx=15, pady=15)
        
        self.model_size = ctk.CTkOptionMenu(
            self.settings_frame, 
            values=["base (快)", "small (平衡)", "medium (推薦)", "large-v3 (最準/慢)"]
        )
        self.model_size.set("medium (推薦)") 
        self.model_size.pack(side="left", padx=10)

        # 按鈕區域
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.pack(pady=10, padx=20, fill="x")

        # 執行按鈕
        self.run_btn = ctk.CTkButton(
            self.button_frame, 
            text="開始轉錄", 
            command=self.start_transcription, 
            fg_color="#106A43", 
            hover_color="#0C5032", 
            height=45, 
            font=("Arial", 16, "bold")
        )
        self.run_btn.pack(side="left", padx=5, fill="x", expand=True)

        # 取消按鈕
        self.cancel_btn = ctk.CTkButton(
            self.button_frame, 
            text="取消", 
            command=self.cancel_transcription,
            fg_color="#8B0000", 
            hover_color="#660000",
            height=45,
            font=("Arial", 16, "bold"),
            state="disabled",
            width=100
        )
        self.cancel_btn.pack(side="left", padx=5)

        # 進度條
        self.progressbar = ctk.CTkProgressBar(self)
        self.progressbar.pack(pady=8, padx=20, fill="x")
        self.progressbar.set(0)

        # 狀態標籤
        self.status_label = ctk.CTkLabel(self, text="準備就緒")
        self.status_label.pack(pady=2)

        # 時間標籤
        self.time_label = ctk.CTkLabel(self, text="", text_color="gray", font=("Arial", 11))
        self.time_label.pack(pady=2)

        # 輸出日誌區
        self.log_box = ctk.CTkTextbox(self, height=200)
        self.log_box.pack(pady=10, padx=20, fill="both", expand=True)
        self.log_box.insert("0.0", "--- 等待執行 ---\n")
        self.log_box.insert("end", "提示：\n")
        self.log_box.insert("end", "• 選擇 medium 或 large 模型可獲得最佳中文辨識效果\n")
        self.log_box.insert("end", "• 支援批次處理多個檔案\n")
        self.log_box.insert("end", "• 處理過程中可隨時取消\n")

    def select_file(self):
        """選擇單一檔案"""
        filetypes = (("Audio files", "*.mp3 *.wav *.m4a *.mp4"), ("All files", "*.*"))
        path = filedialog.askopenfilename(title="選擇音訊檔案", filetypes=filetypes)
        if path:
            self.file_paths = [path]
            self.file_label.configure(text=os.path.basename(path), text_color="white")
            self.log(f"已載入: {os.path.basename(path)}")

    def select_batch_files(self):
        """批次選擇多個檔案"""
        filetypes = (("Audio files", "*.mp3 *.wav *.m4a *.mp4"), ("All files", "*.*"))
        paths = filedialog.askopenfilenames(title="選擇多個音訊檔案", filetypes=filetypes)
        if paths:
            self.file_paths = list(paths)
            file_count = len(self.file_paths)
            self.file_label.configure(
                text=f"已選擇 {file_count} 個檔案", 
                text_color="white"
            )
            self.log(f"\n批次載入 {file_count} 個檔案:")
            for path in self.file_paths:
                self.log(f"  • {os.path.basename(path)}")

    def log(self, message):
        """輸出日誌訊息"""
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")

    def update_status(self, text):
        """更新狀態文字"""
        self.status_label.configure(text=text)

    def update_time_label(self, text):
        """更新時間標籤"""
        self.time_label.configure(text=text)

    def cancel_transcription(self):
        """取消轉錄"""
        self.cancel_flag = True
        self.update_status("正在取消...")
        self.log("⚠ 使用者要求取消操作")

    def start_transcription(self):
        """開始轉錄"""
        if not self.file_paths:
            messagebox.showwarning("錯誤", "請先選擇檔案")
            return
        
        if self.is_running:
            return

        self.is_running = True
        self.cancel_flag = False
        self.run_btn.configure(state="disabled", text="處理中...")
        self.cancel_btn.configure(state="normal")
        self.progressbar.set(0)
        self.update_time_label("")
        
        # 啟動背景執行緒
        thread = threading.Thread(target=self.process_audio, daemon=True)
        thread.start()

    def get_device_config(self):
        """根據作業系統自動選擇最佳裝置設定"""
        system = platform.system()
        machine = platform.machine()
        
        if system == "Darwin":  # macOS
            if machine == "arm64":  # Apple Silicon (M1/M2/M3/M4)
                self.log("✓ 偵測到 Apple Silicon，使用 Metal GPU 加速")
                return {
                    "device": "cpu",  # faster-whisper 在 macOS 上使用 "cpu" 但會利用 Metal
                    "compute_type": "int8",
                    "cpu_threads": 8,
                    "num_workers": 4
                }
            else:  # Intel Mac
                self.log("✓ 偵測到 Intel Mac，使用 CPU 運算")
                return {
                    "device": "cpu",
                    "compute_type": "int8"
                }
        
        # elif system == "Windows":  # Windows
        #     try:
        #         import torch
        #         if torch.cuda.is_available():
        #             self.log("✓ 偵測到 NVIDIA GPU，使用 CUDA 加速")
        #             return {
        #                 "device": "cuda",
        #                 "compute_type": "float16"
        #             }
        #         else:
        #             self.log("✓ 未偵測到 GPU，使用 CPU 運算")
        #             return {
        #                 "device": "cpu",
        #                 "compute_type": "int8"
        #             }
        #     except ImportError:
        #         self.log("⚠ 未安裝 PyTorch，使用 CPU 運算")
        #         return {
        #             "device": "cpu",
        #             "compute_type": "int8"
        #         }
        
        # else:  # Linux 或其他系統
        #     try:
        #         import torch
        #         if torch.cuda.is_available():
        #             self.log("✓ 偵測到 NVIDIA GPU，使用 CUDA 加速")
        #             return {
        #                 "device": "cuda",
        #                 "compute_type": "float16"
        #             }
        #         else:
        #             self.log("✓ 使用 CPU 運算")
        #             return {
        #                 "device": "cpu",
        #                 "compute_type": "int8"
        #             }
        #     except ImportError:
        #         self.log("✓ 使用 CPU 運算")
        #         return {
        #             "device": "cpu",
        #             "compute_type": "int8"
        #         }
            
    def process_audio(self):
        """處理音訊（支援批次）"""
        try:
            # 載入模型（只載入一次）- 針對 Apple Silicon 優化
            if self.model is None:
                selection = self.model_size.get()
                model_name = selection.split(" ")[0]
                
                self.update_status(f"正在載入 Whisper 模型: {model_name}...")
                self.log(f"\n正在載入模型 {model_name} (初次執行需下載模型，請稍候)...")
                self.progressbar.set(0.05)
                
                # 取得最佳裝置設定
                device_config = self.get_device_config()

                self.model = WhisperModel(model_name, **device_config)
                
                self.log("✓ 模型載入完成")
            
            # 批次處理所有檔案
            total_files = len(self.file_paths)
            successful = 0
            
            for idx, file_path in enumerate(self.file_paths):
                if self.cancel_flag:
                    self.log("\n✖ 批次處理已取消")
                    break
                
                self.current_file_index = idx
                self.log(f"\n{'='*60}")
                self.log(f"處理檔案 {idx+1}/{total_files}: {os.path.basename(file_path)}")
                self.log(f"{'='*60}")
                
                # 處理單一檔案
                if self.process_single_file(file_path, total_files, idx):
                    successful += 1
            
            # 最終結果
            if not self.cancel_flag:
                self.progressbar.set(1.0)
                self.update_status("全部完成！")
                self.update_time_label("")
                self.log(f"\n{'='*60}")
                self.log(f"✓ 批次處理完成！成功: {successful}/{total_files}")
                self.log(f"{'='*60}")
                
                messagebox.showinfo(
                    "完成", 
                    f"批次處理完成！\n\n成功處理: {successful} 個檔案\n總共: {total_files} 個檔案"
                )

        except Exception as e:
            self.log(f"\n✖ 錯誤: {str(e)}")
            messagebox.showerror("發生錯誤", f"執行過程中發生錯誤:\n{str(e)}")
        
        finally:
            self.is_running = False
            self.cancel_flag = False
            self.run_btn.configure(state="normal", text="開始轉錄")
            self.cancel_btn.configure(state="disabled")
            self.update_time_label("")

    def process_single_file(self, file_path, total_files, file_idx):
        """處理單一檔案"""
        try:
            # 檢查檔案是否存在
            if not os.path.exists(file_path):
                self.log(f"✖ 檔案不存在: {file_path}")
                return False
            
            self.start_time = time.time()
            
            self.update_status(f"轉錄中 ({file_idx+1}/{total_files}): {os.path.basename(file_path)}")
            
            # 執行轉錄
            segments, info = self.model.transcribe(
                file_path, 
                beam_size=5, 
                language="zh",
                initial_prompt="這是一段繁體中文的對話，請使用台灣地區的用詞。每個句子盡量保持簡短*最多只能有18個字，請在適當的地方斷句*，適合字幕顯示。"
            )
            
            transcribed_text = ""
            srt_content = ""
            segment_id = 1
            total_duration = info.duration if info.duration > 0 else 1

            # 處理每個片段
            for segment in segments:
                # 檢查取消
                if self.cancel_flag:
                    self.log("✖ 處理已取消")
                    return False
                
                # 計算總進度（考慮批次）
                batch_base_progress = file_idx / total_files
                file_progress = (segment.end / total_duration) / total_files
                total_progress = batch_base_progress + file_progress
                
                # 限制在 0-1 之間
                total_progress = max(0.05, min(0.95, total_progress))
                self.progressbar.set(total_progress)
                
                # 計算預估時間
                elapsed_time = time.time() - self.start_time
                progress_ratio = segment.end / total_duration
                
                if progress_ratio > 0.05:  # 至少處理 5% 再估算
                    estimated_file_time = elapsed_time / progress_ratio
                    remaining_file_time = estimated_file_time - elapsed_time
                    
                    # 估算整個批次的剩餘時間
                    avg_time_per_file = elapsed_time / (progress_ratio)
                    remaining_files = total_files - file_idx - 1
                    total_remaining = remaining_file_time + (remaining_files * avg_time_per_file)
                    
                    elapsed_str = str(timedelta(seconds=int(elapsed_time)))
                    remaining_str = str(timedelta(seconds=int(total_remaining)))
                    
                    time_text = f"已用: {elapsed_str} | 預估剩餘: {remaining_str}"
                    self.after(0, self.update_time_label, time_text)

                # 繁簡轉換
                original_text = segment.text
                traditional_text = self.cc.convert(original_text)
                
                # 轉換為全形標點符號
                punctuation_map = {
                    ',': '，', '.': '。', '!': '！', '?': '？',
                    ';': '；', ':': '：', '(': '（', ')': '）',
                    '[': '「', ']': '」', '{': '『', '}': '』',
                    '"': '」', "'": '」', '-': '－', '~': '～',
                }
                for half, full in punctuation_map.items():
                    traditional_text = traditional_text.replace(half, full)

                # 格式化時間
                start_time = self.format_time(segment.start)
                end_time = self.format_time(segment.end)
                
               # 在逗號和頓號處斷句
                text_lines = []
                current_text = traditional_text.strip()
                
                # 先按逗號和頓號分割
                parts = re.split(r'([，？。])', current_text)
                temp_line = ""
                
                for part in parts:
                    if not part:
                        continue
                    
                    # 如果是標點符號，加到當前行後斷行
                    if part in '，？。':
                        if temp_line:
                            text_lines.append(temp_line.strip())
                            temp_line = ""
                    else:
                        # 累積文字
                        temp_line += part
                
                # 處理剩餘文字
                if temp_line.strip():
                    text_lines.append(temp_line.strip())
                
                # 如果沒有分割結果，使用原文
                if not text_lines:
                    text_lines = [current_text]
                
                # TXT 格式：保持單行但移除句尾標點
                clean_text = traditional_text.strip().rstrip('，。！？、；：,.!?;:')
                transcribed_text += f"[{start_time}] {clean_text}\n"
                
                # SRT 格式：使用分行後的結果
                srt_text = '\n'.join(text_lines).strip().rstrip('，。！？、；：,.!?;:')
                srt_content += f"{segment_id}\n{start_time} --> {end_time}\n{srt_text}\n\n"
                
                # 輸出到日誌（顯示所有內容）
                if len(text_lines) > 1:
                    self.log(f"[{start_time}] (共{len(text_lines)}行)")
                    for idx, line in enumerate(text_lines, 1):
                        self.log(f"  第{idx}行: {line}")
                else:
                    self.log(f"[{start_time}] {text_lines[0] if text_lines else clean_text}")
                segment_id += 1

            # 儲存檔案
            base_name = os.path.splitext(file_path)[0]
            srt_filename = f"{base_name}_cht.srt"
            txt_filename = f"{base_name}_cht.txt"
            
            with open(srt_filename, "w", encoding="utf-8") as f:
                f.write(srt_content)
            
            with open(txt_filename, "w", encoding="utf-8") as f:
                f.write(transcribed_text)

            self.log(f"✓ 字幕檔已儲存: {os.path.basename(srt_filename)}")
            self.log(f"✓ 純文字檔已儲存: {os.path.basename(txt_filename)}")
            
            return True

        except Exception as e:
            self.log(f"✖ 處理失敗: {str(e)}")
            return False

    def format_time(self, seconds):
        """將秒數轉為 SRT 時間格式 (HH:MM:SS,mmm)"""
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        ms = int((s - int(s)) * 1000)
        return f"{int(h):02}:{int(m):02}:{int(s):02},{ms:03}"

if __name__ == "__main__":
    app = TranscriberApp()
    app.mainloop()