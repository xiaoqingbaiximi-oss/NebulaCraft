"""多模态处理服务"""
import os
import io
import json
import base64
import time
from server.config import OUTPUT_DIR


class MultiModal:
    def __init__(self):
        self.supported_video = ["mp4", "avi", "mov", "mkv", "webm"]
        self.supported_audio = ["mp3", "wav", "ogg", "flac", "m4a"]
        self.supported_3d = ["stl", "obj", "glb", "gltf"]

    def extract_video_frames(self, file_data, max_frames=5):
        """提取视频关键帧"""
        try:
            from PIL import Image
            import tempfile

            # 保存临时文件
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
                f.write(file_data)
                tmp_path = f.name

            # 使用 ffmpeg 提取帧
            import subprocess
            output_dir = tempfile.mkdtemp()
            subprocess.run([
                "ffmpeg", "-i", tmp_path,
                "-vf", f"fps=1/{max_frames}",
                "-frames:v", str(max_frames),
                f"{output_dir}/frame_%d.jpg",
            ], capture_output=True, timeout=30)

            frames = []
            for i in range(1, max_frames + 1):
                frame_path = os.path.join(output_dir, f"frame_{i}.jpg")
                if os.path.exists(frame_path):
                    with open(frame_path, "rb") as f:
                        frames.append(base64.b64encode(f.read()).decode())

            os.unlink(tmp_path)
            import shutil
            shutil.rmtree(output_dir)

            return {
                "ok": True,
                "frames": frames,
                "count": len(frames),
            }
        except ImportError:
            return {"ok": False, "error": "需要安装 ffmpeg"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def transcribe_audio(self, file_data, language="zh"):
        """音频转写"""
        try:
            import tempfile
            import subprocess

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(file_data)
                tmp_path = f.name

            # 使用 whisper 转写
            result = subprocess.run([
                "whisper", tmp_path,
                "--language", language,
                "--model", "tiny",
                "--output_format", "json",
                "--output_dir", os.path.dirname(tmp_path),
            ], capture_output=True, text=True, timeout=120)

            os.unlink(tmp_path)

            return {"ok": True, "text": result.stdout[:5000]}
        except FileNotFoundError:
            return {"ok": False, "error": "需要安装 whisper: pip install openai-whisper"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def preview_3d_model(self, file_data, fmt):
        """3D 模型预览信息"""
        return {
            "ok": True,
            "format": fmt,
            "size": len(file_data),
            "preview_url": None,
            "info": f"3D 模型: {fmt.upper()}, {len(file_data) / 1024:.1f} KB",
            "tip": "使用在线查看器: https://3dviewer.net",
        }

    def screen_analyze(self, image_data):
        """屏幕截图分析"""
        try:
            from PIL import Image
            import io as io_module

            img = Image.open(io_module.BytesIO(image_data))
            return {
                "ok": True,
                "size": f"{img.width}x{img.height}",
                "mode": img.mode,
                "suggestion": "使用 AI 对话进行详细分析",
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def camera_analyze(self, image_data):
        """摄像头实时分析"""
        return self.screen_analyze(image_data)


multimodal = MultiModal()