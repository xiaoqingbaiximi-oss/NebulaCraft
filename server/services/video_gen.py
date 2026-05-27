"""
内置视频生成引擎
支持: 文字动画 / 幻灯片 / 数字人口播 / 字幕生成
纯本地运行，不依赖外部 API
"""
import os
import json
import time
import subprocess
import tempfile
from PIL import Image, ImageDraw, ImageFont
from server.config import OUTPUT_DIR

VIDEO_DIR = os.path.join(OUTPUT_DIR, "videos")
os.makedirs(VIDEO_DIR, exist_ok=True)


class VideoGenEngine:
    def __init__(self):
        self.ffmpeg_available = self._check_ffmpeg()

    def _check_ffmpeg(self):
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
            return True
        except:
            return False

    def generate_text_animation(self, text, duration=5, style="fade"):
        """文字动画视频"""
        if not self.ffmpeg_available:
            return {"ok": False, "error": "需要安装 ffmpeg"}

        fps = 24
        total_frames = duration * fps
        width, height = 1280, 720

        tmp_dir = tempfile.mkdtemp()
        frames = []

        for i in range(total_frames):
            img = Image.new("RGB", (width, height), (20, 20, 40))
            draw = ImageDraw.Draw(img)

            # 背景动画
            for y in range(height):
                ratio = y / height
                r = int(20 + (108 - 20) * ratio)
                g = int(20 + (92 - 20) * ratio)
                b = int(40 + (231 - 40) * ratio)
                draw.line([(0, y), (width, y)], fill=(r, g, b))

            # 文字动画
            progress = i / total_frames
            alpha = min(255, int(255 * (1 - abs(progress - 0.5) * 2)))
            font_size = int(48 + 20 * math.sin(progress * math.pi))

            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()

            bbox = draw.textbbox((0, 0), text, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            x = (width - tw) // 2
            y = int(height // 2 + 50 * math.sin(progress * math.pi * 2))

            # 发光效果
            for offset in range(3, 0, -1):
                draw.text((x - offset, y - offset), text,
                         fill=(108, 92, 231, alpha // (offset + 1)), font=font)
            draw.text((x, y), text, fill=(255, 255, 255), font=font)

            frame_path = os.path.join(tmp_dir, f"frame_{i:04d}.png")
            img.save(frame_path)
            frames.append(frame_path)

        # 合成视频
        output_file = os.path.join(VIDEO_DIR, f"anim_{int(time.time() * 1000)}.mp4")
        subprocess.run([
            "ffmpeg", "-y", "-framerate", str(fps),
            "-i", os.path.join(tmp_dir, "frame_%04d.png"),
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
            output_file,
        ], capture_output=True, timeout=60)

        # 清理
        import shutil
        shutil.rmtree(tmp_dir)

        return {"ok": True, "url": f"/output/videos/{os.path.basename(output_file)}",
                "duration": duration, "type": "text_animation"}

    def generate_slideshow(self, image_paths, duration_per_image=3):
        """幻灯片视频"""
        if not self.ffmpeg_available:
            return {"ok": False, "error": "需要安装 ffmpeg"}

        if not image_paths:
            return {"ok": False, "error": "请提供图片路径"}

        output_file = os.path.join(VIDEO_DIR, f"slides_{int(time.time() * 1000)}.mp4")

        # 创建图片列表
        list_file = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
        for path in image_paths:
            if os.path.exists(path):
                list_file.write(f"file '{os.path.abspath(path)}'\n")
                list_file.write(f"duration {duration_per_image}\n")
        list_file.close()

        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", list_file.name,
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            output_file,
        ], capture_output=True, timeout=120)

        os.unlink(list_file.name)
        return {"ok": True, "url": f"/output/videos/{os.path.basename(output_file)}",
                "duration": len(image_paths) * duration_per_image, "type": "slideshow"}

    def generate_subtitles(self, text, output_srt=True):
        """生成字幕文件"""
        srt_content = ""
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if line.strip():
                start = f"00:{i // 60:02d}:{i % 60:02d},000"
                end = f"00:{(i + 3) // 60:02d}:{(i + 3) % 60:02d},000"
                srt_content += f"{i + 1}\n{start} --> {end}\n{line.strip()}\n\n"

        file_id = f"subtitle_{int(time.time() * 1000)}.srt"
        filepath = os.path.join(VIDEO_DIR, file_id)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(srt_content)

        return {"ok": True, "url": f"/output/videos/{file_id}",
                "lines": len([l for l in lines if l.strip()]), "type": "subtitle"}


video_gen = VideoGenEngine()