"""
PDF 处理 API - 增强版
支持: 合并 / 提取文字 / 拆分 / 图片转PDF / 元数据
"""
import io
import os
import time
from server.config import OUTPUT_DIR


def handle_merge(file_list):
    """合并多个 PDF"""
    if not file_list:
        return {"ok": False, "error": "请上传至少2个PDF文件"}
    
    try:
        from PyPDF2 import PdfReader, PdfWriter
        
        writer = PdfWriter()
        total_pages = 0
        
        for file_data in file_list:
            reader = PdfReader(io.BytesIO(file_data))
            for page in reader.pages:
                writer.add_page(page)
                total_pages += 1
        
        buf = io.BytesIO()
        writer.write(buf)
        
        file_id = f"merged_{int(time.time() * 1000)}.pdf"
        filepath = os.path.join(OUTPUT_DIR, file_id)
        with open(filepath, "wb") as f:
            f.write(buf.getvalue())
        
        return {
            "ok": True,
            "url": f"/output/{file_id}",
            "filename": file_id,
            "total_pages": total_pages,
            "file_count": len(file_list),
            "size": f"{len(buf.getvalue()) / 1024:.1f} KB",
        }
    
    except ImportError:
        return {"ok": False, "error": "需要安装 PyPDF2: pip install PyPDF2"}
    except Exception as e:
        return {"ok": False, "error": f"PDF合并失败: {e}"}


def handle_extract_text(file_data):
    """提取 PDF 文字"""
    try:
        from PyPDF2 import PdfReader
        
        reader = PdfReader(io.BytesIO(file_data))
        total_pages = len(reader.pages)
        text_parts = []
        
        for i, page in enumerate(reader.pages[:50]):  # 最多50页
            t = page.extract_text()
            if t:
                text_parts.append(f"--- 第{i+1}页 ---\n{t}")
        
        full_text = "\n\n".join(text_parts)
        
        return {
            "ok": True,
            "text": full_text[:50000],  # 限制5万字
            "pages": total_pages,
            "extracted_pages": len(text_parts),
            "truncated": len(full_text) > 50000,
        }
    
    except ImportError:
        return {"ok": False, "error": "需要安装 PyPDF2"}
    except Exception as e:
        return {"ok": False, "error": f"PDF文字提取失败: {e}"}


def handle_split(file_data, page_range=None):
    """拆分 PDF"""
    try:
        from PyPDF2 import PdfReader, PdfWriter
        
        reader = PdfReader(io.BytesIO(file_data))
        total = len(reader.pages)
        
        # 解析页码范围：1-3,5,7-9
        pages_to_extract = set()
        if page_range:
            parts = page_range.split(",")
            for part in parts:
                if "-" in part:
                    start, end = part.split("-")
                    pages_to_extract.update(range(int(start) - 1, min(int(end), total)))
                else:
                    pages_to_extract.add(int(part) - 1)
        else:
            # 默认提取第一页
            pages_to_extract = {0}
        
        writer = PdfWriter()
        for i in sorted(pages_to_extract):
            if 0 <= i < total:
                writer.add_page(reader.pages[i])
        
        buf = io.BytesIO()
        writer.write(buf)
        
        file_id = f"split_{int(time.time() * 1000)}.pdf"
        filepath = os.path.join(OUTPUT_DIR, file_id)
        with open(filepath, "wb") as f:
            f.write(buf.getvalue())
        
        return {
            "ok": True,
            "url": f"/output/{file_id}",
            "extracted_pages": list(sorted(pages_to_extract)),
            "total_pages": total,
        }
    
    except ImportError:
        return {"ok": False, "error": "需要安装 PyPDF2"}
    except Exception as e:
        return {"ok": False, "error": f"PDF拆分失败: {e}"}


def handle_metadata(file_data):
    """读取 PDF 元数据"""
    try:
        from PyPDF2 import PdfReader
        
        reader = PdfReader(io.BytesIO(file_data))
        meta = reader.metadata
        
        info = {
            "pages": len(reader.pages),
            "title": meta.get("/Title", "未知"),
            "author": meta.get("/Author", "未知"),
            "subject": meta.get("/Subject", ""),
            "creator": meta.get("/Creator", ""),
            "producer": meta.get("/Producer", ""),
            "created": meta.get("/CreationDate", ""),
            "modified": meta.get("/ModDate", ""),
        }
        
        return {"ok": True, "metadata": info}
    
    except ImportError:
        return {"ok": False, "error": "需要安装 PyPDF2"}
    except Exception as e:
        return {"ok": False, "error": str(e)}