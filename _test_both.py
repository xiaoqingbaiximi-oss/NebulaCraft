import sys, traceback 
sys.path.insert(0, 'E:/NebulaCraft') 
try: 
    from server.services.cloud_image import generate_image 
    r = generate_image('test', 512, 512, 'дʵ') 
    print('cloud_image OK:', r.get('url')) 
except Exception as e: 
    print('cloud_image ERROR:') 
    traceback.print_exc() 
print('---') 
try: 
    from server.services.image_gen import image_gen 
    r = image_gen.generate('test', 'art', 512, 512) 
    print('image_gen OK:', r.get('url')) 
except Exception as e: 
    print('image_gen ERROR:') 
    traceback.print_exc() 
