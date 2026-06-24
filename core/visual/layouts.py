import random

LAYOUT_VERSION = "v1.0"

# Standard comic page resolution (2:3 aspect ratio)
PAGE_WIDTH = 1024
PAGE_HEIGHT = 1536
GUTTER = 20  # Spacing between panels and edges

LAYOUTS = {
    # 5 Panels: 1 large top, 2 mid, 2 bottom
    "layout_5_standard": {
        "width": PAGE_WIDTH,
        "height": PAGE_HEIGHT,
        "panels": [
            {"bbox": [GUTTER, GUTTER, PAGE_WIDTH - GUTTER, 500], "fit": "cover", "anchor": "center"},
            {"bbox": [GUTTER, 500 + GUTTER, (PAGE_WIDTH // 2) - (GUTTER // 2), 1000], "fit": "cover", "anchor": "top"},
            {"bbox": [(PAGE_WIDTH // 2) + (GUTTER // 2), 500 + GUTTER, PAGE_WIDTH - GUTTER, 1000], "fit": "cover", "anchor": "center"},
            {"bbox": [GUTTER, 1000 + GUTTER, (PAGE_WIDTH // 2) - (GUTTER // 2), PAGE_HEIGHT - GUTTER], "fit": "cover", "anchor": "center"},
            {"bbox": [(PAGE_WIDTH // 2) + (GUTTER // 2), 1000 + GUTTER, PAGE_WIDTH - GUTTER, PAGE_HEIGHT - GUTTER], "fit": "cover", "anchor": "center"}
        ]
    },
    # 4 Panels: 1 wide top, 2 mid, 1 wide bottom
    "layout_4_cinematic": {
        "width": PAGE_WIDTH,
        "height": PAGE_HEIGHT,
        "panels": [
            {"bbox": [GUTTER, GUTTER, PAGE_WIDTH - GUTTER, 400], "fit": "cover", "anchor": "center"},
            {"bbox": [GUTTER, 400 + GUTTER, (PAGE_WIDTH // 2) - (GUTTER // 2), 1100], "fit": "cover", "anchor": "top"},
            {"bbox": [(PAGE_WIDTH // 2) + (GUTTER // 2), 400 + GUTTER, PAGE_WIDTH - GUTTER, 1100], "fit": "cover", "anchor": "center"},
            {"bbox": [GUTTER, 1100 + GUTTER, PAGE_WIDTH - GUTTER, PAGE_HEIGHT - GUTTER], "fit": "cover", "anchor": "center"}
        ]
    },
    # 3 Panels: 3 vertical wide slices (Webtoon style)
    "layout_3_webtoon": {
        "width": PAGE_WIDTH,
        "height": PAGE_HEIGHT,
        "panels": [
            {"bbox": [GUTTER, GUTTER, PAGE_WIDTH - GUTTER, (PAGE_HEIGHT // 3) - GUTTER], "fit": "cover", "anchor": "center"},
            {"bbox": [GUTTER, (PAGE_HEIGHT // 3) + GUTTER, PAGE_WIDTH - GUTTER, (2 * PAGE_HEIGHT // 3) - GUTTER], "fit": "cover", "anchor": "center"},
            {"bbox": [GUTTER, (2 * PAGE_HEIGHT // 3) + GUTTER, PAGE_WIDTH - GUTTER, PAGE_HEIGHT - GUTTER], "fit": "cover", "anchor": "center"}
        ]
    },
    # 6 Panels: 2 top, 2 mid, 2 bottom
    "layout_6_dense": {
        "width": PAGE_WIDTH,
        "height": PAGE_HEIGHT,
        "panels": [
            {"bbox": [GUTTER, GUTTER, (PAGE_WIDTH // 2) - (GUTTER // 2), 500], "fit": "cover", "anchor": "center"},
            {"bbox": [(PAGE_WIDTH // 2) + (GUTTER // 2), GUTTER, PAGE_WIDTH - GUTTER, 500], "fit": "cover", "anchor": "center"},
            {"bbox": [GUTTER, 500 + GUTTER, (PAGE_WIDTH // 2) - (GUTTER // 2), 1000], "fit": "cover", "anchor": "center"},
            {"bbox": [(PAGE_WIDTH // 2) + (GUTTER // 2), 500 + GUTTER, PAGE_WIDTH - GUTTER, 1000], "fit": "cover", "anchor": "center"},
            {"bbox": [GUTTER, 1000 + GUTTER, (PAGE_WIDTH // 2) - (GUTTER // 2), PAGE_HEIGHT - GUTTER], "fit": "cover", "anchor": "center"},
            {"bbox": [(PAGE_WIDTH // 2) + (GUTTER // 2), 1000 + GUTTER, PAGE_WIDTH - GUTTER, PAGE_HEIGHT - GUTTER], "fit": "cover", "anchor": "center"}
        ]
    }
}

def get_best_layout_for_panel_count(count):
    """Returns a layout ID that perfectly matches the requested number of panels."""
    valid_layouts = [k for k, v in LAYOUTS.items() if len(v["panels"]) == count]
    if not valid_layouts:
        # Fallback if the planner outputs a weird number
        if count <= 3: return "layout_3_webtoon"
        if count == 4: return "layout_4_cinematic"
        if count == 5: return "layout_5_standard"
        return "layout_6_dense"
    
    return random.choice(valid_layouts)
