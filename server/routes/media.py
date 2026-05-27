"""
媒体处理 API - 增强版
支持: 压缩 / 格式转换 / 去水印 / 高清修复 / 二维码解码 / 图片信息
"""
import io
import os
import time
import base64
from PIL import Image, ImageEnhance, ImageFilter
from server.config import OUTPUT_DIR
from server.utils.security import sanitize_filename


def handle_upload(action, file_data, filename, params):
    """路由分发"""
    if action == "compress":
        quality = int(params.get("quality", 70))
        return compress_image(file_data, filename, quality)
    
    if action == "convert":
        target = params.get("format", "png")
        return convert_image(file_data, filename, target)
    
    if action == "qr_decode":
        return decode_qr(file_data)
    
    if action == "info":
        return get_image_info(file_data, filename)
    
    return {"ok": False, "error": f"未知操作: {action}"}


def compress_image(file_data, filename, quality=70):
    """压缩图片"""
    try:
        img = Image.open(io.BytesIO(file_data))
        buf = io.BytesIO()
        
        # 智能选择格式
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGBA')
            save_format = 'PNG'
            ext = 'png'
        else:
            img = img.convert('RGB')
            save_format = 'JPEG'
            ext = 'jpg'
        
        if save_format == 'JPEG':
            img.save(buf, format=save_format, quality=quality, optimize=True)
        else:
            img.save(buf, format=save_format, optimize=True)
        
        fid = f"compressed_{int(time.time() * 1000)}.{ext}"
        fp = os.path.join(OUTPUT_DIR, fid)
        with open(fp, "wb") as f:
            f.write(buf.getvalue())
        
        original = len(file_data)
        compressed = len(buf.getvalue())
        ratio = round((1 - compressed / original) * 100, 1)
        
        return {
            "ok": True,
            "url": f"/output/{fid}",
            "original": original,
            "compressed": compressed,
            "saved": f"{ratio}%",
            "format": ext,
        }
    except Exception as e:
        return {"ok": False, "error": f"压缩失败: {e}"}


def convert_image(file_data, filename, target_format):
    """格式转换"""
    try:
        img = Image.open(io.BytesIO(file_data))
        target = target_format.lower()
        
        valid_formats = {"png", "jpg", "jpeg", "webp", "bmp", "gif", "tiff"}
        if target not in valid_formats:
            return {"ok": False, "error": f"不支持的格式: {target}，支持: {', '.join(valid_formats)}"}
        
        buf = io.BytesIO()
        
        # 处理透明度
        if target in ("jpg", "jpeg", "bmp"):
            if img.mode in ("RGBA", "P"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "RGBA":
                    background.paste(img, mask=img.split()[3])
                else:
                    background.paste(img)
                img = background
            img = img.convert("RGB")
        
        save_format = "JPEG" if target in ("jpg", "jpeg") else target.upper()
        img.save(buf, format=save_format, quality=90)
        
        fid = f"converted_{int(time.time() * 1000)}.{target}"
        fp = os.path.join(OUTPUT_DIR, fid)
        with open(fp, "wb") as f:
            f.write(buf.getvalue())
        
        return {
            "ok": True,
            "url": f"/output/{fid}",
            "format": target,
            "size": f"{img.width}x{img.height}",
        }
    except Exception as e:
        return {"ok": False, "error": f"转换失败: {e}"}


def handle_remove_watermark(file_data, filename):
    """智能去水印"""
    try:
        img = Image.open(io.BytesIO(file_data))
        w, h = img.size
        
        # 多区域尝试：底部10%、右下角20%
        regions = [
            (0, 0, w, int(h * 0.9)),           # 裁剪底部10%
            (0, 0, int(w * 0.85), h),          # 裁剪右侧15%
            (0, 0, int(w * 0.85), int(h * 0.9)),  # 裁剪右下角
        ]
        
        fid = f"nowm_{int(time.time() * 1000)}.png"
        fp = os.path.join(OUTPUT_DIR, fid)
        
        # 默认使用底部裁剪
        cropped = img.crop(regions[0])
        buf = io.BytesIO()
        cropped.save(buf, format="PNG")
        with open(fp, "wb") as f:
            f.write(buf.getvalue())
        
        return {
            "ok": True,
            "url": f"/output/{fid}",
            "method": "底部裁剪",
            "note": "如需更精确的去水印，建议使用专业工具",
        }
    except Exception as e:
        return {"ok": False, "error": f"去水印失败: {e}"}


def handle_enhance(file_data, filename):
    """高清修复：2倍放大 + 锐化 + 对比度增强"""
    try:
        img = Image.open(io.BytesIO(file_data))
        original_size = f"{img.width}x{img.height}"
        
        # 2倍放大
        w, h = img.size
        img = img.resize((w * 2, h * 2), Image.LANCZOS)
        
        # 锐化
        img = ImageEnhance.Sharpness(img).enhance(1.8)
        
        # 对比度增强
        img = ImageEnhance.Contrast(img).enhance(1.2)
        
        # 色彩增强
        img = ImageEnhance.Color(img).enhance(1.1)
        
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        
        fid = f"enhanced_{int(time.time() * 1000)}.png"
        fp = os.path.join(OUTPUT_DIR, fid)
        with open(fp, "wb") as f:
            f.write(buf.getvalue())
        
        return {
            "ok": True,
            "url": f"/output/{fid}",
            "original_size": original_size,
            "enhanced_size": f"{img.width}x{img.height}",
        }
    except Exception as e:
        return {"ok": False, "error": f"高清修复失败: {e}"}


def decode_qr(file_data):
    """二维码解码"""
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(file_data))
        
        try:
            from pyzbar.pyzbar import decode
            results = decode(img)
            if results:
                decoded_data = []
                for r in results:
                    decoded_data.append({
                        "data": r.data.decode("utf-8", "ignore"),
                        "type": r.type,
                    })
                return {"ok": True, "results": decoded_data}
            return {"ok": False, "error": "未检测到二维码"}
        except ImportError:
            return {"ok": False, "error": "需安装 pyzbar: pip install pyzbar"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def get_image_info(file_data, filename):
    """获取图片详细信息"""
    try:
        img = Image.open(io.BytesIO(file_data))
        
        info = {
            "filename": filename,
            "format": img.format,
            "mode": img.mode,
            "size": f"{img.width}x{img.height}",
            "aspect_ratio": f"{img.width / img.height:.2f}",
            "file_size": f"{len(file_data) / 1024:.1f} KB",
            "dpi": img.info.get("dpi", "未知"),
        }
        
        # EXIF 信息
        exif = img.getexif()
        if exif:
            info["exif"] = {}
            for tag_id, value in exif.items():
                if tag_id in (271, 272, 306):  # 设备、型号、拍摄时间
                    info["exif"][str(tag_id)] = str(value)
        
        return {"ok": True, "info": info}
    except Exception as e:
        return {"ok": False, "error": str(e)}