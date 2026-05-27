import sys, traceback 
sys.path.insert(0, 'E:/NebulaCraft') 
from server.services.image_gen import image_gen 
try: 
    r = image_gen.generate('test', 'art', 512, 512) 
    print('OK:', r.get('url')) 
except: 
    traceback.print_exc() 
