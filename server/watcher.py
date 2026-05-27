"""热文件夹监控 - 自动加入知识库"""
import os
import time
import threading
from server.config import DATA_DIR
from server.services.knowledge import kb

WATCH_DIR = os.path.join(DATA_DIR, "watch")
os.makedirs(WATCH_DIR, exist_ok=True)


class FolderWatcher:
    def __init__(self):
        self.running = False
        self.thread = None
        self.processed = set()
        self.collection = "watch_folder"
    
    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.thread.start()
        print(f"📁 热文件夹监控已启动: {WATCH_DIR}")
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
    
    def _watch_loop(self):
        while self.running:
            try:
                self._scan()
            except Exception as e:
                print(f"监控错误: {e}")
            time.sleep(5)  # 每5秒扫描一次
    
    def _scan(self):
        if not os.path.exists(WATCH_DIR):
            return
        
        for filename in os.listdir(WATCH_DIR):
            filepath = os.path.join(WATCH_DIR, filename)
            
            # 跳过隐藏文件和已处理的
            if filename.startswith(".") or filepath in self.processed:
                continue
            
            if not os.path.isfile(filepath):
                continue
            
            # 只处理文本文件
            ext = filename.split(".")[-1].lower() if "." in filename else ""
            if ext not in ("txt", "md", "csv", "json", "py", "js", "html", "css", "log", "yaml", "xml", "pdf"):
                continue
            
            try:
                # 读取文件
                if ext == "pdf":
                    text = self._read_pdf(filepath)
                else:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        text = f.read()
                
                if text and len(text) > 10:
                    # 加入知识库
                    kb.add_document(
                        collection_name=self.collection,
                        text=text,
                        title=filename,
                        source=f"watch:{filepath}",
                    )
                    print(f"📁 已加入知识库: {filename}")
                
                self.processed.add(filepath)
            except Exception as e:
                print(f"处理文件失败 {filename}: {e}")
    
    def _read_pdf(self, filepath):
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(filepath)
            text = ""
            for page in reader.pages[:10]:
                t = page.extract_text()
                if t:
                    text += t + "\n"
            return text
        except:
            return ""


watcher = FolderWatcher()