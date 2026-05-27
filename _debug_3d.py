from server.services.td_engine import td_engine 
import os 
url = '/output/ai_images/art_1779426109763.png' 
img_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(td_engine.__class__.__module__))), 'data', url.lstrip('/')) 
print('img_path:', img_path) 
print('exists:', os.path.exists(img_path)) 
