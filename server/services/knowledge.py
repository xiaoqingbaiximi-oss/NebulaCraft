"""
知识库服务 - RAG (检索增强生成)
支持: 文本 / PDF / 网页 导入
"""
import os
import json
import hashlib
import time
import io
from server.config import DATA_DIR

KB_DIR = os.path.join(DATA_DIR, "knowledge_base")
os.makedirs(KB_DIR, exist_ok=True)


class KnowledgeBase:

    def __init__(self):
        self.collections = {}
        self._load_collections()

    def _load_collections(self):
        meta_file = os.path.join(KB_DIR, "collections.json")
        if os.path.exists(meta_file):
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    self.collections = json.load(f)
            except:
                self.collections = {}

    def _save_collections(self):
        meta_file = os.path.join(KB_DIR, "collections.json")
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(self.collections, f, ensure_ascii=False, indent=2)

    def create_collection(self, name, description=""):
        if name in self.collections:
            return {"ok": False, "error": f"集合「{name}」已存在"}
        collection_dir = os.path.join(KB_DIR, name)
        os.makedirs(collection_dir, exist_ok=True)
        self.collections[name] = {
            "name": name,
            "description": description,
            "document_count": 0,
            "chunk_count": 0,
            "created": time.strftime("%Y-%m-%d %H:%M:%S"),
            "updated": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        self._save_collections()
        return {"ok": True, "message": f"集合「{name}」已创建"}

    def delete_collection(self, name):
        if name not in self.collections:
            return {"ok": False, "error": "集合不存在"}
        import shutil
        collection_dir = os.path.join(KB_DIR, name)
        if os.path.exists(collection_dir):
            shutil.rmtree(collection_dir)
        del self.collections[name]
        self._save_collections()
        return {"ok": True, "message": f"集合「{name}」已删除"}

    def list_collections(self):
        result = []
        for name, meta in self.collections.items():
            result.append({
                "name": name,
                "description": meta.get("description", ""),
                "documents": meta.get("document_count", 0),
                "chunks": meta.get("chunk_count", 0),
                "updated": meta.get("updated", ""),
            })
        return {"ok": True, "collections": sorted(result, key=lambda x: x["updated"], reverse=True)}

    def add_document(self, collection_name, text, title="", source="", metadata=None):
        if collection_name not in self.collections:
            return {"ok": False, "error": "集合不存在"}

        doc_id = hashlib.md5(f"{title}_{text[:100]}_{time.time()}".encode()).hexdigest()[:12]
        chunks = self._chunk_text(text, chunk_size=500, overlap=50)

        chunk_data = []
        for i, chunk in enumerate(chunks):
            embedding = self._get_embedding(chunk)
            chunk_data.append({
                "id": f"{doc_id}_{i}",
                "doc_id": doc_id,
                "chunk_index": i,
                "text": chunk,
                "embedding": embedding,
            })

        doc_file = os.path.join(KB_DIR, collection_name, f"{doc_id}.json")
        doc_data = {
            "id": doc_id,
            "title": title or f"文档_{doc_id}",
            "source": source,
            "metadata": metadata or {},
            "chunks": chunk_data,
            "chunk_count": len(chunks),
            "text_length": len(text),
            "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        with open(doc_file, "w", encoding="utf-8") as f:
            json.dump(doc_data, f, ensure_ascii=False, indent=2)

        self.collections[collection_name]["document_count"] += 1
        self.collections[collection_name]["chunk_count"] += len(chunks)
        self.collections[collection_name]["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
        self._save_collections()

        return {"ok": True, "doc_id": doc_id, "chunks": len(chunks), "title": title or f"文档_{doc_id}"}

    # ===== PDF 导入 =====
    def import_pdf(self, collection_name, file_data, filename):
        """导入 PDF 文件"""
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(io.BytesIO(file_data))
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
            if not text.strip():
                return {"ok": False, "error": "PDF 无法提取文本（可能是扫描版）"}
            return self.add_document(collection_name, text, title=filename, source="PDF")
        except ImportError:
            return {"ok": False, "error": "需要安装 PyPDF2: pip install PyPDF2"}
        except Exception as e:
            return {"ok": False, "error": f"PDF 解析失败: {str(e)}"}

    # ===== 网页导入 =====
    def import_url(self, collection_name, url):
        """导入网页内容"""
        try:
            import requests
            from bs4 import BeautifulSoup
            resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0 (compatible; NebulaCraft/1.0)"})
            resp.encoding = resp.apparent_encoding or "utf-8"
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
            title = soup.title.string.strip() if soup.title else url
            # 限制最大 50000 字符
            text = text[:50000]
            return self.add_document(collection_name, text, title=title, source=url)
        except ImportError:
            return {"ok": False, "error": "需要安装 beautifulsoup4 和 requests: pip install beautifulsoup4 requests"}
        except Exception as e:
            return {"ok": False, "error": f"网页爬取失败: {str(e)}"}

    def search(self, collection_name, query, top_k=5, min_score=0.3):
        if collection_name not in self.collections:
            return {"ok": False, "error": "集合不存在"}

        query_embedding = self._get_embedding(query)
        if not query_embedding:
            return {"ok": True, "results": [], "message": "无法生成查询向量"}

        all_results = []
        collection_dir = os.path.join(KB_DIR, collection_name)

        if not os.path.exists(collection_dir):
            return {"ok": True, "results": [], "message": "集合目录不存在"}

        for filename in os.listdir(collection_dir):
            if not filename.endswith(".json"):
                continue
            filepath = os.path.join(collection_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    doc = json.load(f)
                for chunk in doc.get("chunks", []):
                    if chunk.get("embedding"):
                        score = self._cosine_similarity(query_embedding, chunk["embedding"])
                        if score >= min_score:
                            all_results.append({
                                "doc_id": chunk["doc_id"],
                                "title": doc.get("title", ""),
                                "chunk_index": chunk["chunk_index"],
                                "text": chunk["text"],
                                "score": round(score, 4),
                                "source": doc.get("source", ""),
                            })
            except:
                continue

        all_results.sort(key=lambda x: x["score"], reverse=True)
        return {"ok": True, "results": all_results[:top_k], "total_found": len(all_results), "query": query}

    def delete_document(self, collection_name, doc_id):
        if collection_name not in self.collections:
            return {"ok": False, "error": "集合不存在"}
        doc_file = os.path.join(KB_DIR, collection_name, f"{doc_id}.json")
        if not os.path.exists(doc_file):
            return {"ok": False, "error": "文档不存在"}
        try:
            with open(doc_file, "r", encoding="utf-8") as f:
                doc = json.load(f)
            chunk_count = doc.get("chunk_count", 0)
        except:
            chunk_count = 0
        os.remove(doc_file)
        self.collections[collection_name]["document_count"] = max(0, self.collections[collection_name]["document_count"] - 1)
        self.collections[collection_name]["chunk_count"] = max(0, self.collections[collection_name]["chunk_count"] - chunk_count)
        self.collections[collection_name]["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
        self._save_collections()
        return {"ok": True, "message": f"文档「{doc_id}」已删除"}

    def get_stats(self):
        total_docs = sum(c.get("document_count", 0) for c in self.collections.values())
        total_chunks = sum(c.get("chunk_count", 0) for c in self.collections.values())
        return {"ok": True, "stats": {"collections": len(self.collections), "total_documents": total_docs, "total_chunks": total_chunks}}

    # ===== 内部方法 =====
    def _chunk_text(self, text, chunk_size=500, overlap=50):
        paragraphs = text.split("\n\n")
        chunks = []
        current = ""
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            if len(current) + len(para) < chunk_size:
                current += para + "\n\n"
            else:
                if current.strip():
                    chunks.append(current.strip())
                if len(para) > chunk_size:
                    sentences = para.replace("。", "。\n").replace("！", "！\n").replace("？", "？\n").split("\n")
                    sub_chunk = ""
                    for sent in sentences:
                        if len(sub_chunk) + len(sent) < chunk_size:
                            sub_chunk += sent
                        else:
                            if sub_chunk.strip():
                                chunks.append(sub_chunk.strip())
                            sub_chunk = sent
                    current = (sub_chunk + "\n\n") if sub_chunk.strip() else ""
                else:
                    current = para + "\n\n"
        if current.strip():
            chunks.append(current.strip())
        if not chunks:
            chunks = [text]
        return chunks

    def _get_embedding(self, text):
        try:
            import requests
            resp = requests.post(
                "http://localhost:11434/api/embeddings",
                json={"model": "nomic-embed-text", "prompt": text[:2000]},
                timeout=30,
            )
            if resp.status_code == 200:
                return resp.json().get("embedding", [])
        except:
            pass
        return self._fallback_embedding(text)

    def _fallback_embedding(self, text, dims=128):
        hash_bytes = hashlib.sha256(text.encode()).digest()
        vector = []
        for i in range(dims):
            byte_val = hash_bytes[i % len(hash_bytes)]
            vector.append((byte_val / 255.0) * 2 - 1)
        norm = sum(v * v for v in vector) ** 0.5
        if norm > 0:
            vector = [v / norm for v in vector]
        return vector

    def _cosine_similarity(self, a, b):
        min_len = min(len(a), len(b))
        a, b = a[:min_len], b[:min_len]
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(y * y for y in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)


kb = KnowledgeBase()