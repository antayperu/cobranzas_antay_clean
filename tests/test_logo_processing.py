
import unittest
import os
from PIL import Image, ImageDraw
import sys

# Add parent dir to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import image_processor

class TestLogoProcessing(unittest.TestCase):
    
    def setUp(self):
        # Create a dummy image with whitespace
        self.test_img_path = "test_logo_input.png"
        self.processed_img_path = "test_logo_output.png"
        
        # Create 1000x1000 image, white background
        img = Image.new('RGB', (1000, 1000), color='white')
        d = ImageDraw.Draw(img)
        # Draw a red rectangle in the center (size 200x100), simulating the actual logo content
        # Position: 400, 450 to 600, 550
        d.rectangle([400, 450, 600, 550], fill='red')
        img.save(self.test_img_path)

    def tearDown(self):
        if os.path.exists(self.test_img_path):
            os.remove(self.test_img_path)
        if os.path.exists(self.processed_img_path):
            os.remove(self.processed_img_path)

    def test_trim_and_resize(self):
        with open(self.test_img_path, 'rb') as f:
            img_bytes = f.read()

        # Process with target width 720 (Retina for 360px display)
        # The content is 200x100. Aspect ratio 2:1.
        # After trim, should be approx 200x100.
        # Resize to width 720 -> height should be 360.
        # BUT max height constraint might apply. 
        # Requirement: Target height max: 110px. (Wait, is this for the *display* or the *file*?)
        # User said: "Target width: 360px (retina: guardar a 720px ... Target height max: 110px ...)"
        # Assuming the 110px max height is for the DISPLAY size (1x). So file size max height 220px.
        
        processed_bytes, width, height = image_processor.process_logo_image(img_bytes)
        
        # Write to file to check transparency/format if needed
        with open(self.processed_img_path, 'wb') as f:
            f.write(processed_bytes)
            
        with Image.open(self.processed_img_path) as res_img:
            # Check dimensions
            # Original content ratio 2:1.
            # If width target is 720, height would be 360. 
            # But max height constraint (220px for retina file) should cap it.
            # So height should be 220, width should be 440.
            
            print(f"Result Size: {res_img.size}")
            self.assertTrue(res_img.width <= 720)
            self.assertTrue(res_img.height <= 220) 
            self.assertTrue(width <= 720)
            self.assertTrue(height <= 220)

if __name__ == '__main__':
    unittest.main()
