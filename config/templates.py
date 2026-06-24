# config/templates.py

"""Layout templates for the Dynamic Panel Layout System.

Each template defines a canvas size and a list of panels. The `res` field
specifies the *native* resolution that the Stable Diffusion / Animagine model
must generate for that panel. The `coords` field gives the top‑left corner
position (x, y) where the panel image should be pasted onto the master canvas.

The design respects the strict constraint: **NO CROPPING OR RESIZING**. Images
must be generated at exactly the resolution defined here; the compositor will
simply paste them onto the canvas.
"""

LAYOUTS = {
    "1_panel_splash": {
        "canvas_size": {"width": 896, "height": 1152},
        "panels": [
            {
                "id": "panel_1",
                "res": {"width": 896, "height": 1152},
                "coords": {"x": 0, "y": 0},
            }
        ],
    },
    "3_panel_action": {
        "canvas_size": {"width": 896, "height": 1152},
        "panels": [
            {
                "id": "panel_1",
                "res": {"width": 896, "height": 384},
                "coords": {"x": 0, "y": 0},
            },
            {
                "id": "panel_2",
                "res": {"width": 896, "height": 384},
                "coords": {"x": 0, "y": 384},
            },
            {
                "id": "panel_3",
                "res": {"width": 896, "height": 384},
                "coords": {"x": 0, "y": 768},
            },
        ],
    },
    "4_panel_grid": {
        "canvas_size": {"width": 896, "height": 1152},
        "panels": [
            {
                "id": "panel_1",
                "res": {"width": 448, "height": 576},
                "coords": {"x": 0, "y": 0},
            },
            {
                "id": "panel_2",
                "res": {"width": 448, "height": 576},
                "coords": {"x": 448, "y": 0},
            },
            {
                "id": "panel_3",
                "res": {"width": 448, "height": 576},
                "coords": {"x": 0, "y": 576},
            },
            {
                "id": "panel_4",
                "res": {"width": 448, "height": 576},
                "coords": {"x": 448, "y": 576},
            },
        ],
    },
}
