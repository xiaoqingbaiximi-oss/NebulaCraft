# -*- coding: utf-8 -*- 
from server.services.ollama import chat 
import time 
start=time.time() 
try: 
    reply = chat([{"role":"user","content":"hi"}], model="deepseek-chat", timeout=30) 
    print("Time:", round(time.time()-start,1), "s") 
    print("Reply:", reply[:100]) 
except Exception as e: 
    print("Error:", e) 
