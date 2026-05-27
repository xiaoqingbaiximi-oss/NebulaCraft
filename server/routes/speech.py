"""
文字转语音 API - 增强版
支持: edge-tts / 多音色 / 语速调节 / 音频缓存 / 批量生成
"""
import os
import subprocess
import time
import hashlib
import json
from server.config import OUTPUT_DIR, DATA_DIR

# 语音缓存目录
SPEECH_CACHE = os.path.join(DATA_DIR, "speech_cache")
os.makedirs(SPEECH_CACHE, exist_ok=True)

# 可用音色
VOICES = {
    "zh-CN-XiaoxiaoNeural": {"name": "晓晓", "gender": "女", "style": "温柔"},
    "zh-CN-YunxiNeural": {"name": "云希", "gender": "男", "style": "活泼"},
    "zh-CN-YunjianNeural": {"name": "云健", "gender": "男", "style": "稳重"},
    "zh-CN-XiaoyiNeural": {"name": "晓依", "gender": "女", "style": "可爱"},
    "zh-CN-YunyangNeural": {"name": "云扬", "gender": "男", "style": "新闻"},
    "zh-CN-XiaochenNeural": {"name": "晓辰", "gender": "女", "style": "温柔"},
    "en-US-JennyNeural": {"name": "Jenny", "gender": "女", "style": "美式英语"},
    "en-US-GuyNeural": {"name": "Guy", "gender": "男", "style": "美式英语"},
    "en-GB-SoniaNeural": {"name": "Sonia", "gender": "女", "style": "英式英语"},
}


def handle(body):
    text = body.get("text", "").strip()
    voice = body.get("voice", "zh-CN-XiaoxiaoNeural")
    rate = body.get("rate", "+0%")     # 语速: -50% ~ +100%
    pitch = body.get("pitch", "+0Hz")  # 音调: -20Hz ~ +20Hz
    list_voices = body.get("list_voices", False)
    
    # 列出音色
    if list_voices:
        voice_list = []
        for vid, info in VOICES.items():
            voice_list.append({
                "id": vid,
                "name": info["name"],
                "gender": info["gender"],
                "style": info["style"],
            })
        return {"ok": True, "voices": voice_list}
    
    if not text:
        return {"ok": False, "error": "请输入要转换的文字"}
    
    if len(text) > 5000:
        return {"ok": False, "error": "文字过长，请控制在5000字以内"}
    
    # 检查缓存
    cache_key = hashlib.md5(f"{text}_{voice}_{rate}_{pitch}".encode()).hexdigest()
    cache_file = os.path.join(SPEECH_CACHE, f"{cache_key}.mp3")
    
    if os.path.exists(cache_file):
        file_id = f"tts_{cache_key[:12]}.mp3"
        # 复制到输出目录
        import shutil
        output_file = os.path.join(OUTPUT_DIR, file_id)
        shutil.copy2(cache_file, output_file)
        return {
            "ok": True,
            "url": f"/output/{file_id}",
            "text": text[:100] + ("..." if len(text) > 100 else ""),
            "voice": VOICES.get(voice, {}).get("name", voice),
            "cached": True,
        }
    
    # 验证音色
    if voice not in VOICES:
        voice = "zh-CN-XiaoxiaoNeural"
    
    try:
        # 调用 edge-tts
        rate_str = rate if rate.startswith(("+", "-")) else f"+{rate}%" if rate.isdigit() else rate
        pitch_str = pitch if pitch.startswith(("+", "-")) else f"+{pitch}Hz" if pitch.replace("-", "").isdigit() else pitch
        
        cmd = [
            "edge-tts",
            "--voice", voice,
            "--rate", rate_str,
            "--pitch", pitch_str,
            "--text", text,
            "--write-media", cache_file,
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )
        
        if result.returncode != 0:
            if "not found" in result.stderr.lower():
                return {"ok": False, "error": "请安装 edge-tts: pip install edge-tts"}
            return {"ok": False, "error": f"语音合成失败: {result.stderr[:200]}"}
        
        # 复制到输出目录
        file_id = f"tts_{cache_key[:12]}.mp3"
        import shutil
        output_file = os.path.join(OUTPUT_DIR, file_id)
        shutil.copy2(cache_file, output_file)
        
        return {
            "ok": True,
            "url": f"/output/{file_id}",
            "text": text[:100] + ("..." if len(text) > 100 else ""),
            "voice": VOICES.get(voice, {}).get("name", voice),
            "cached": False,
        }
    
    except FileNotFoundError:
        return {"ok": False, "error": "请安装 edge-tts: pip install edge-tts"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "语音合成超时，文字可能过长"}
    except Exception as e:
        return {"ok": False, "error": f"语音合成失败: {e}"}


def handle_ssml(body):
    """SSML 合成（支持更多控制）"""
    ssml = body.get("ssml", "").strip()
    voice = body.get("voice", "zh-CN-XiaoxiaoNeural")
    
    if not ssml:
        return {"ok": False, "error": "请输入 SSML"}
    
    # 包装 SSML
    full_ssml = f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="zh-CN">{ssml}</speak>'
    
    cache_key = hashlib.md5(f"{full_ssml}_{voice}".encode()).hexdigest()
    cache_file = os.path.join(SPEECH_CACHE, f"{cache_key}.mp3")
    
    try:
        import tempfile
        ssml_file = tempfile.NamedTemporaryFile(mode='w', suffix='.ssml', delete=False, encoding='utf-8')
        ssml_file.write(full_ssml)
        ssml_file.close()
        
        cmd = [
            "edge-tts",
            "--voice", voice,
            "--file", ssml_file.name,
            "--write-media", cache_file,
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        os.unlink(ssml_file.name)
        
        if result.returncode != 0:
            return {"ok": False, "error": "SSML 合成失败"}
        
        import shutil
        file_id = f"tts_{cache_key[:12]}.mp3"
        output_file = os.path.join(OUTPUT_DIR, file_id)
        shutil.copy2(cache_file, output_file)
        
        return {"ok": True, "url": f"/output/{file_id}"}
    
    except Exception as e:
        return {"ok": False, "error": str(e)}