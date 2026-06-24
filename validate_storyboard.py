import json
import os
import sys

def main():
    # Attempt to load templates
    try:
        from config.templates import LAYOUTS
    except ImportError:
        print("❌ Error: Could not import LAYOUTS from config.templates.")
        sys.exit(1)

    if len(sys.argv) > 1:
        storyboard_path = sys.argv[1]
    else:
        storyboard_path = os.path.join("output", "storyboard.json")

    if not os.path.exists(storyboard_path):
        print(f"⚠️  No storyboard found at {storyboard_path}. Nothing to validate.")
        return

    with open(storyboard_path, "r", encoding="utf-8") as f:
        try:
            pages = json.load(f)
        except json.JSONDecodeError as e:
            print(f"❌ Error: Invalid JSON in storyboard.json: {e}")
            sys.exit(1)

    if not isinstance(pages, list):
        print("❌ Error: storyboard.json must contain a list of pages.")
        sys.exit(1)

    errors = 0
    print(f"Validating {len(pages)} pages against layout templates...\n")

    for pg in pages:
        page_id = pg.get("id", f"page_{pg.get('page_number', 'unknown')}")
        layout_id = pg.get("layout_template")
        
        if not layout_id:
            print(f"❌ {page_id}: Missing 'layout_template'")
            errors += 1
            continue
            
        if layout_id not in LAYOUTS:
            print(f"❌ {page_id}: Unknown layout_template '{layout_id}'")
            errors += 1
            continue
            
        template = LAYOUTS[layout_id]
        expected_panels = len(template.get("panels", []))
        panels = pg.get("panels", [])
        actual_panels = len(panels)
        
        if actual_panels != expected_panels:
            print(f"❌ {page_id}: Template '{layout_id}' requires {expected_panels} panels, but found {actual_panels}.")
            errors += 1
        else:
            print(f"✅ {page_id}: {layout_id} ({actual_panels}/{expected_panels} panels)")

    print(f"\nValidation Complete. Errors found: {errors}")
    if errors > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
