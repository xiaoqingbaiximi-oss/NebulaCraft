"""HTTP request handler - stable"""
import json, os, re, time, traceback
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from server.config import BASE_DIR, VERSION, DEBUG, RATE_LIMIT_ENABLED, RATE_LIMIT_MAX_REQUESTS, RATE_LIMIT_WINDOW, MAX_UPLOAD_SIZE, MAX_BODY_SIZE
from server.utils.security import safe_path
from server.utils.helpers import get_local_ip
from server.routes import calculator, generator, security, image, files, chat, translate, share, auth, smart, speech, poster, extra, more, media, models, scraper, notes, rss, pdf
from server.routes import knowledge as kb_routes
from server.routes import agent as agent_routes
from server.routes import plugin as plugin_routes
from server.routes import sd as sd_routes
from server.routes import export as export_routes
from server.routes import audit as audit_routes
from server.routes import quota as quota_routes
from server.routes import search as search_routes
from server.routes import mailer as mailer_routes
from server.routes import crypto as crypto_routes
from server.routes import multimodal as multimodal_routes
from server.routes import automation as automation_routes
from server.routes import dev as dev_routes
from server.routes import collab as collab_routes
from server.routes import marketplace as marketplace_routes
from server.routes import federated as federated_routes
from server.routes import quantum as quantum_routes
from server.routes import neural as neural_routes
from server.routes import autonomous as autonomous_routes
from server.routes import metaverse as metaverse_routes
from server.routes import db_api as db_api_routes
from server.routes import image_gen_routes
from server.routes import video_gen_routes
from server.routes import code_routes
from server.routes import td_routes
from server.routes import music_routes
from server.routes import scheduler_routes
from server.routes import workflow_routes
from server.routes import settings_routes
from server.services.scheduler import start_scheduler
from server.services.workflow import start_workflow_engine

_rate_limit = {}

class Handler(BaseHTTPRequestHandler):
    def log(self, msg):
        if DEBUG: print(f"[{time.strftime('%H:%M:%S')}] {self.client_address[0]} {msg}")

    def do_GET(self):
        path = urlparse(self.path).path
        if not self._check_rate(): return
        try:
            if path.startswith(("/output/","/static/","/css/","/js/","/locales/")):
                if path.startswith("/output/"):
                    path = "/data" + path
                return self._serve_static(path)
            if path in ("/manifest.json","/sw.js","/favicon.ico"): return self._serve_static(path)
            if path.startswith("/share/"): return self._serve_share(path)
            if path == "/": return self._serve_index()
            if path == "/docs": return self._serve_docs()
            if path == "/health": return self._send_json({"status":"healthy","version":VERSION,"ip":get_local_ip()})
            if path == "/api/models/list": return self._send_json(models.handle_list())
            if path == "/api/sd_status": return self._send_json(sd_routes.handle_status({}))
            if path == "/api/sd_styles": return self._send_json(sd_routes.handle_styles({}))
            if path == "/api/knowledge":
                try: return self._send_json(kb_routes.handle({"action":"get_stats"}))
                except: return self._send_json({"ok":True,"stats":{"collections":0,"total_documents":0,"total_chunks":0}})
            if path == "/api/plugin":
                try: return self._send_json(plugin_routes.handle({"action":"list"}))
                except: return self._send_json({"ok":True,"plugins":[]})
            if path == "/api/agent/tools": return self._send_json(agent_routes.handle_list_tools({}))
            if path == "/api/quota": return self._send_json(quota_routes.handle({"action":"check"}))
            if path == "/api/audit": return self._send_json(audit_routes.handle({"action":"stats"}))
            if path == "/api/marketplace": return self._send_json(marketplace_routes.handle({"action":"stats"}))
            if path == "/api/dev": return self._send_json(dev_routes.handle({"action":"openapi"}))
            if path == "/api/collab": return self._send_json(collab_routes.handle({"action":"list_teams"}))
            if path == "/api/scheduler/list": return self._send_json(scheduler_routes.handle({"action":"list"}))
            if path == "/api/workflow/list": return self._send_json(workflow_routes.handle({"action":"list"}))
            if path.startswith("/api/3d/download/"):
                task_id = path.split("/")[-1]
                return td_routes.handle_3d_download(self, task_id)
            return self._serve_index()
        except Exception as e:
            self.log(f"GET error {path}: {e}")
            try: self._send_json({"ok":False,"error":"Internal error"},500)
            except: pass

    def do_OPTIONS(self):
        self._set_cors(); self.send_response(204); self.end_headers()

    def do_POST(self):
        path = urlparse(self.path).path
        if not self._check_rate(): return
        ct = self.headers.get("Content-Type","")
        try:
            if "multipart/form-data" in ct: return self._handle_multipart(path)
            body = self._read_body()
            if body is None: return self._send_json({"ok":False,"error":"Body too large"},413)
            routes = {
                "/api/chat":lambda:chat.handle(body),"/api/chat_search":lambda:chat.handle_search(body),
                "/api/calculator":lambda:calculator.handle(body),"/api/generator":lambda:generator.handle(body),
                "/api/security":lambda:security.handle(body),"/api/generate_image":lambda:image.handle_generate(body),
                "/api/translate":lambda:translate.handle(body),"/api/register":lambda:auth.handle_register(body),
                "/api/login":lambda:auth.handle_login(body),"/api/share":lambda:share.handle_create(body),
                "/api/smart":lambda:smart.handle(body),"/api/speech":lambda:speech.handle(body),
                "/api/poster":lambda:poster.handle(body),"/api/extra":lambda:extra.handle(body),
                "/api/more":lambda:more.handle(body),"/api/models/pull":lambda:models.handle_pull(body),
                "/api/scraper":lambda:scraper.handle(body),"/api/notes":lambda:notes.handle(body),
                "/api/rss":lambda:rss.handle(body),"/api/knowledge":lambda:kb_routes.handle(body),
                "/api/agent":lambda:agent_routes.handle(body),"/api/agent/plan":lambda:agent_routes.handle_plan(body),
                "/api/agent/tools":lambda:agent_routes.handle_list_tools(body),
                "/api/plugin":lambda:plugin_routes.handle(body),"/api/sd_image":lambda:sd_routes.handle(body),
                "/api/sd_status":lambda:sd_routes.handle_status(body),"/api/sd_styles":lambda:sd_routes.handle_styles(body),
                "/api/export":lambda:export_routes.handle(body),"/api/audit":lambda:audit_routes.handle(body),
                "/api/quota":lambda:quota_routes.handle(body),"/api/search":lambda:search_routes.handle(body),
                "/api/mailer":lambda:mailer_routes.handle(body),"/api/crypto":lambda:crypto_routes.handle(body),
                "/api/multimodal":lambda:multimodal_routes.handle(body),"/api/automation":lambda:automation_routes.handle(body),
                "/api/dev":lambda:dev_routes.handle(body),"/api/collab":lambda:collab_routes.handle(body),
                "/api/marketplace":lambda:marketplace_routes.handle(body),"/api/federated":lambda:federated_routes.handle(body),
                "/api/quantum":lambda:quantum_routes.handle(body),"/api/neural":lambda:neural_routes.handle(body),
                "/api/autonomous":lambda:autonomous_routes.handle(body),"/api/metaverse":lambda:metaverse_routes.handle(body),
                "/api/db/query":lambda:db_api_routes.handle(body),"/api/image_gen":lambda:image_gen_routes.handle(body),
                "/api/video_gen":lambda:video_gen_routes.handle(body),"/api/code":lambda:code_routes.handle(body),
                "/api/3d/generate":lambda:td_routes.handle_3d_generate(self, body),
                "/api/music":lambda:music_routes.handle(body),
                "/api/scheduler":lambda:scheduler_routes.handle(body),
                "/api/workflow":lambda:workflow_routes.handle(body),
                "/api/settings":lambda:settings_routes.handle(body),
            }
            if path == "/api/chat_stream": return self._handle_stream(body)
            handler = routes.get(path)
            if handler:
                try: return self._send_json(handler())
                except Exception as e:
                    self.log(f"Route error {path}: {e}")
                    return self._send_json({"ok":False,"error":str(e)},500)
            self._send_json({"ok":False,"error":"Route not found"},404)
        except Exception as e:
            self.log(f"POST error {path}: {e}")
            try: self._send_json({"ok":False,"error":"Internal error"},500)
            except: pass

    def _handle_stream(self, body):
        self.send_response(200); self.send_header("Content-Type","text/event-stream")
        self.send_header("Cache-Control","no-cache"); self.send_header("Connection","keep-alive")
        self.send_header("X-Accel-Buffering","no"); self._set_cors(); self.end_headers()
        try:
            gen = chat.handle_stream(body)
            for chunk in gen():
                try: self.wfile.write(chunk.encode()); self.wfile.flush()
                except: break
        except Exception as e: self.log(f"Stream error: {e}")

    def _handle_multipart(self, path):
        length = int(self.headers.get("Content-Length",0))
        if length > MAX_UPLOAD_SIZE: return self._send_json({"ok":False,"error":"File too large"},413)
        try: form = self._parse_multipart()
        except: return self._send_json({"ok":False,"error":"Parse error"})
        fd = form.get("file")
        if not fd: return self._send_json({"ok":False,"error":"No file"})
        filename = form.get("filename","file.bin")
        if path == "/api/file_analyze": return self._send_json(files.handle_analyze(fd, filename))
        if path == "/api/file_upload": return self._send_json(files.handle_upload(fd, filename))
        if path == "/api/remove_bg": return self._send_json(image.handle_remove_bg(fd, filename))
        if path == "/api/ocr": return self._send_json(image.handle_ocr(fd))
        if path.startswith("/api/media"):
            qs = urlparse(self.path).query; params = parse_qs(qs)
            action = params.get("action",[""])[0]
            if action == "watermark": return self._send_json(media.handle_remove_watermark(fd, filename))
            if action == "enhance": return self._send_json(media.handle_enhance(fd, filename))
            return self._send_json(media.handle_upload(action, fd, filename, {"format":params.get("format",["png"])[0]}))
        return self._send_json({"ok":False,"error":"Unknown upload"},404)

    def _serve_share(self, path):
        share_id = path.split("/")[-1]; data = share.handle_get(share_id)
        if data.get("ok"):
            content = data.get("content","").replace("<","&lt;").replace(">","&gt;")
            html = f"<!DOCTYPE html><html lang='zh'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Share</title><style>body{{font-family:sans-serif;max-width:680px;margin:40px auto;padding:20px;background:#0a0a14;color:#e8e8f8;line-height:1.8}}h2{{color:#a78bfa}}pre{{background:#1a1a35;padding:20px;border-radius:12px;white-space:pre-wrap}}p{{color:#6b6b80;text-align:center;margin-top:20px;font-size:.8rem}}</style></head><body><h2>Shared Content</h2><pre>{content}</pre><p>{data.get('time','')} - NebulaCraft</p></body></html>"
        else: html = "<!DOCTYPE html><html lang='zh'><head><meta charset='UTF-8'><title>Not Found</title><style>body{{font-family:sans-serif;text-align:center;padding:80px 20px;background:#0a0a14;color:#e8e8f8}}</style></head><body><h2>Share not found</h2></body></html>"
        content = html.encode("utf-8")
        try:
            self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8")
            self.send_header("Content-Length",str(len(content))); self.end_headers(); self.wfile.write(content)
        except: pass

    def _serve_index(self):
        try: return self._serve_file(os.path.join(BASE_DIR,"index.html"),"text/html; charset=utf-8")
        except: pass

    def _serve_docs(self):
        from server.routes.docs import handle_index
        html = handle_index(); content = html.encode("utf-8")
        try:
            self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8")
            self.send_header("Content-Length",str(len(content))); self.end_headers(); self.wfile.write(content)
        except: pass

    def _serve_static(self, path):
        fp = safe_path(BASE_DIR, path)
        if not fp or not os.path.isfile(fp): self.send_error(404); return
        cts = {".html":"text/html; charset=utf-8",".css":"text/css; charset=utf-8",".js":"application/javascript; charset=utf-8",".json":"application/json; charset=utf-8",".png":"image/png",".jpg":"image/jpeg",".jpeg":"image/jpeg",".svg":"image/svg+xml",".ico":"image/x-icon",".mp3":"audio/mpeg",".woff2":"font/woff2",".gif":"image/gif",".webp":"image/webp",".mid":"audio/midi",".midi":"audio/midi"}
        ext = os.path.splitext(fp)[1].lower(); cache = 86400 if ext in('.png','.jpg','.svg','.ico','.woff2','.mp3','.mid','.midi') else 0
        return self._serve_file(fp, cts.get(ext,"application/octet-stream"), cache)

    def _serve_file(self, fp, ct, cache_seconds=0):
        if not os.path.exists(fp): self.send_error(404); return
        try:
            with open(fp,"rb") as f: content = f.read()
            self.send_response(200); self.send_header("Content-Type",ct)
            self.send_header("Content-Length",str(len(content))); self.send_header("Connection","close")
            if cache_seconds > 0: self.send_header("Cache-Control",f"public, max-age={cache_seconds}")
            self._set_cors(); self.end_headers(); self.wfile.write(content)
        except: pass

    def _read_body(self):
        length = int(self.headers.get("Content-Length",0))
        if length == 0: return {}
        if length > MAX_BODY_SIZE: return None
        try: return json.loads(self.rfile.read(length))
        except: return {}

    def _parse_multipart(self):
        ct = self.headers.get("Content-Type",""); length = int(self.headers.get("Content-Length",0))
        body = self.rfile.read(length); bm = re.search(r"boundary=([^;\s]+)", ct)
        if not bm: return {}
        boundary = bm.group(1).encode(); parts = body.split(b"--"+boundary); result = {}
        for part in parts:
            if b'name="file"' in part:
                header_end = part.find(b"\r\n\r\n")
                if header_end == -1: continue
                file_data = part[header_end+4:]; end_marker = file_data.rfind(b"\r\n--")
                if end_marker != -1: file_data = file_data[:end_marker]
                result["file"] = file_data
                fn_match = re.search(rb'filename="([^"]*)"', part)
                if fn_match: result["filename"] = fn_match.group(1).decode("utf-8","ignore")
        return result

    def _send_json(self, data, status=200):
        try:
            resp = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
            self.send_response(status); self.send_header("Content-Type","application/json; charset=utf-8")
            self.send_header("Content-Length",str(len(resp))); self.send_header("Connection","close")
            self._set_cors(); self.end_headers(); self.wfile.write(resp)
        except: pass

    def _set_cors(self):
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Methods","GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers","Content-Type, Authorization")

    def _check_rate(self):
        if not RATE_LIMIT_ENABLED: return True
        ip = self.client_address[0]; now = time.time()
        if ip not in _rate_limit or now > _rate_limit[ip]["reset"]: _rate_limit[ip] = {"count":0,"reset":now+RATE_LIMIT_WINDOW}
        _rate_limit[ip]["count"] += 1
        if _rate_limit[ip]["count"] > RATE_LIMIT_MAX_REQUESTS:
            self.send_response(429); self.send_header("Content-Type","application/json; charset=utf-8")
            self.send_header("Retry-After",str(int(_rate_limit[ip]["reset"]-now))); self.end_headers()
            self.wfile.write(json.dumps({"ok":False,"error":"Rate limited"}).encode()); return False
        return True

    def log_message(self, format, *args):
        if DEBUG: print(f"[{time.strftime('%H:%M:%S')}] {self.client_address[0]} {format % args}")


start_scheduler()
start_workflow_engine()