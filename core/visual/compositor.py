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
        
        # --- Add Narration Text Box ---
        narration = page_metadata["panels"][idx].get("description", "").strip()
        if narration:
            try:
                import textwrap
                # Calculate box dimensions
                panel_w = panel_config["res"]["width"]
                panel_h = panel_config["res"]["height"]
                margin = 20
                
                # Try to use a better font, fallback to default
                try:
                    font = ImageFont.truetype("arial.ttf", 24)
                except IOError:
                    font = ImageFont.load_default()
                
                # Wrap text to fit panel width
                avg_char_width = 12
                chars_per_line = max(10, (panel_w - (margin * 4)) // avg_char_width)
                lines = textwrap.wrap(narration, width=chars_per_line)
                
                line_height = 28
                text_block_height = len(lines) * line_height
                box_height = text_block_height + (margin * 2)
                
                # Position box at the bottom of the panel
                box_x1 = x + margin
                box_y1 = y + panel_h - box_height - margin
                box_x2 = x + panel_w - margin
                box_y2 = y + panel_h - margin
                
                # Draw semi-transparent black background for readability
                overlay = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
                overlay_draw = ImageDraw.Draw(overlay)
                overlay_draw.rectangle([box_x1, box_y1, box_x2, box_y2], fill=(0, 0, 0, 180), outline="white", width=2)
                canvas = Image.alpha_composite(canvas.convert('RGBA'), overlay).convert('RGB')
                
                # We need a new draw object since we created a new canvas image
                draw = ImageDraw.Draw(canvas)
                
                # Draw text lines
                text_y = box_y1 + margin
                for line in lines:
                    draw.text((box_x1 + margin, text_y), line, font=font, fill="white")
                    text_y += line_height
                    
            except Exception as e:
                logger.error(f"Failed to draw narration for panel {idx}: {e}")

    canvas.save(output_path, "PNG")
    logger.info(f"  Saved composite page: {output_path}")
    return bboxes
