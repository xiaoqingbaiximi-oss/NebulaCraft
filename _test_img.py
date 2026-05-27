import sys 
sys.path.insert(0, 'E:/NebulaCraft') 
try: 
    from server.routes.image_gen_routes import handle 
    r = handle({'prompt': 'test', 'style': 'art'}) 
    print('OK:', r.get('url', r.get('error'))) 
except Exception as e: 
    import traceback 
    traceback.print_exc() 
