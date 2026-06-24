import os
from PIL import Image, ImageDraw, ImageFont
import logging
from config.templates import LAYOUTS as LAYOUT_TEMPLATES

logger = logging.getLogger(__name__)

def compose_page(page_metadata: dict, panel_images: list, output_path: str) -> dict:
    """
    Composes a full comic page from individual panel images without any resizing or cropping.
    Expects pre-loaded PIL Image objects in `panel_images` matching the metadata panels array.
    """
    layout_id = page_metadata.get("layout_template")
    if not layout_id or layout_id not in LAYOUT_TEMPLATES:
        logger.error(f"Layout {layout_id} not found in LAYOUT_TEMPLATES. Defaulting to 4_panel_grid.")
        layout_id = "4_panel_grid"
        
    template = LAYOUT_TEMPLATES[layout_id]
    canvas_width = template["canvas_size"]["width"]
    canvas_height = template["canvas_size"]["height"]

    # Create pure black canvas base
    canvas = Image.new('RGB', (canvas_width, canvas_height), color='black')
    draw = ImageDraw.Draw(canvas)
    
    bboxes = {}

    for idx, panel_config in enumerate(template["panels"]):
        if idx >= len(panel_images):
            break
            
        x = panel_config["coords"]["x"]
        y = panel_config["coords"]["y"]
        
        # Load natively generated asset
        panel_img = panel_images[idx]
        
        # CRITICAL: Structural paste completely bypasses resizing or cropping
        canvas.paste(panel_img, (x, y))
        
        # Render manga-style panel sequence tracker
        box_size = 40
        padding = 10
        box_coords = [x + padding, y + padding, x + padding + box_size, y + padding + box_size]
        
        # Draw overlay indicator bounding container
        draw.rectangle(box_coords, fill="white", outline="black", width=3)
        
        # Draw numbering context
        text = str(idx + 1)
        # We try to use a default font or default PIL text rendering
        # Just simple text drawing for Kaggle compatibility
        draw.text((box_coords[0] + 12, box_coords[1] + 8), text, fill="black", stroke_width=1)
        
        panel_id = page_metadata["panels"][idx]["id"]
        # Save bbox for legacy compatibility if needed
        bboxes[panel_id] = [x, y, x + panel_config["res"]["width"], y + panel_config["res"]["height"]]
        
    canvas.save(output_path, "PNG")
    logger.info(f"  Saved composite page: {output_path}")
    return bboxes
