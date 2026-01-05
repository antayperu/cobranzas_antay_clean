
import io
from PIL import Image, ImageChops

def trim(im):
    """
    Trims whitespace from the image.
    Works for both transparent backgrounds (Alpha) and white backgrounds.
    """
    if im.mode != 'RGBA':
        im = im.convert('RGBA')
    
    # Method 1: Get BBox from Alpha channel
    bbox = im.getbbox()
    
    # Method 2: If bbox is full size or simplistic, try checking for white background
    # Create a white background image
    bg = Image.new(im.mode, im.size, (255, 255, 255, 255))
    diff = ImageChops.difference(im, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)
    bbox_white = diff.getbbox()
    
    # If standard bbox (alpha) detected empty space, use it.
    # If the image was solid white background, getbbox() on alpha might return full image.
    # We prefer the smallest non-empty bbox.
    
    final_bbox = bbox
    if bbox and bbox_white:
        # Calculate areas to see which is tighter? 
        # Usually we want the content.
        # If image has alpha transparency, bbox is correct.
        # If image has white background (opacity), bbox is full, bbox_white is content.
        
        # Heuristic: Check corner pixels. If top-left is white/transparent, likely needs trim.
        # For safety and "Enterprise" robustness, we can try to intersect?
        # Actually, let's prioritize Alpha trim first. If the image is opaque, use White trim.
        
        # Check if image has transparency
        extrema = im.getextrema()
        if extrema[3][0] < 255: 
            # Has transparent pixels
            final_bbox = bbox
        else:
            # Opaque image, assume white background needs trimming
            final_bbox = bbox_white
            
    if final_bbox:
        return im.crop(final_bbox)
    return im

def process_logo_image(image_bytes):
    """
    Process image bytes:
    1. Open image
    2. Convert to RGBA
    3. Trim whitespace
    4. Resize to max dimensions (Target: Width 720px, Height 220px - for Retina 2x)
    5. Return bytes (PNG), width, height
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        
        # Trim
        img = trim(img)
        
        # Dimensions Constraints (Retina 2x for Display 360x110)
        MAX_WIDTH = 720
        MAX_HEIGHT = 220 # 110 * 2
        
        width_ratio = MAX_WIDTH / float(img.size[0])
        height_ratio = MAX_HEIGHT / float(img.size[1])
        
        ratio = min(width_ratio, height_ratio)
        
        # Only resize if larger than target (don't upcomplicate small logos, but user wants "Corporate Size")
        # If we upscale small logos they look blurry. Better to keep original if smaller?
        # User said: "Redimensionar a tamaño estándar... Target width: 360px"
        # We will apply resize if it exceeds dimensions OR if it's reasonably close, to standardize.
        # Let's simple cap at max dimensions.
        
        if ratio < 1.0:
            new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Save to bytes
        output = io.BytesIO()
        img.save(output, format='PNG', optimize=True)
        return output.getvalue(), img.width, img.height
        
    except Exception as e:
        print(f"Error processing image: {e}")
        return image_bytes, 0, 0 # Return original on failure
