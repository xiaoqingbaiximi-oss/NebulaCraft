import urllib.request, json 
try: 
    req = urllib.request.Request('http://localhost:8889/api/3d/generate', data=json.dumps({'prompt':'test'}).encode(), headers={'Content-Type':'application/json'}) 
    resp = urllib.request.urlopen(req) 
    print(resp.read().decode()) 
except Exception as e: 
    print('Error:', e) 
    if hasattr(e, 'read'): 
        print(e.read().decode()) 
