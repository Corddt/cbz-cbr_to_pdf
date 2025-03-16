import base64
import os
from PIL import Image, ImageDraw, ImageFont
import io

def generate_icon():
    """Generate a simple icon for the application."""
    # Create a new image with a white background
    img = Image.new('RGBA', (256, 256), color=(255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw a rounded rectangle for the document
    draw.rounded_rectangle([(40, 20), (216, 236)], radius=20, fill=(52, 152, 219))
    
    # Draw a smaller rounded rectangle for the CBZ file
    draw.rounded_rectangle([(70, 50), (186, 150)], radius=10, fill=(41, 128, 185))
    
    # Draw an arrow
    arrow_points = [(128, 160), (100, 190), (156, 190)]
    draw.polygon(arrow_points, fill=(255, 255, 255))
    
    # Draw "PDF" text
    try:
        # Try to use a font if available
        font = ImageFont.truetype("arial.ttf", 40)
    except IOError:
        # Fall back to default font
        font = ImageFont.load_default()
    
    draw.text((100, 195), "PDF", fill=(255, 255, 255), font=font)
    
    # Save the image as ICO
    icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
    img.save(icon_path, format="ICO")
    
    # Also save as PNG for the web version
    web_static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "web_app", "static")
    if os.path.exists(web_static_dir):
        img.save(os.path.join(web_static_dir, "icon.png"), format="PNG")
    
    return icon_path

if __name__ == "__main__":
    icon_path = generate_icon()
    print(f"Icon generated at: {icon_path}") 