import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class StoryboardPlanner:
    """
    Storyboard Planner — Novel Video Factory v5
    Extracts visual narrative beats from text chunks to generate a storyboard sequence grouped by pages.
    """
    def __init__(self, llm_adapter, config: dict = None):
        self.llm = llm_adapter
        self.config = config or {}
        
    def get_system_prompt(self) -> str:
        return """
        You are an expert Manga Director. Your job is to break down a webnovel script into structured Comic Pages.
        For each page, you must select an appropriate layout template from these options:
        - '1_panel_splash': Used for massive epic reveals, establishing shots, or high-impact actions. (Requires exactly 1 panel/beat)
        - '3_panel_action': Used for fast pacing, linear motion, or rapid dialogue transitions. (Requires exactly 3 panels/beats)
        - '4_panel_grid': Used for standard storytelling, balanced pacing, and stable interactions. (Requires exactly 4 panels/beats)
        
        You must strictly output JSON matching the required schema. The number of elements in the 'panels' array MUST exactly match the required panel count of your chosen 'layout_template'. Do not combine panels or use legacy merging fields.
        """

    def get_json_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "state": {
                    "type": "object",
                    "properties": {
                        "current_location": {"type": "string"},
                        "time_of_day": {"type": "string"},
                        "weather": {"type": "string"},
                        "active_characters": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                },
                "pages": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "layout_template": {"type": "string", "enum": ["1_panel_splash", "3_panel_action", "4_panel_grid"]},
                            "reasoning": {"type": "string"},
                            "panels": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "description": {"type": "string"},
                                        "visual_tags": {
                                            "type": "array",
                                            "items": {"type": "string"}
                                        },
                                        "characters": {
                                            "type": "array",
                                            "items": {"type": "string"}
                                        },
                                        "location": {"type": "string"}
                                    },
                                    "required": ["description", "visual_tags"]
                                }
                            }
                        },
                        "required": ["layout_template", "panels"]
                    }
                }
            },
            "required": ["pages"]
        }

    def plan_pages(self, text_chunk: str, current_state: dict, chapter: int = 1, start_page: int = 1, start_sequence: int = 1) -> dict:
        system = self.get_system_prompt()
        schema = self.get_json_schema()
        
        prompt_content = {
            "provided_state": current_state,
            "narrative_block": text_chunk,
            "schema": schema
        }
        
        prompt = json.dumps(prompt_content, indent=2)
        max_t = self.config.get("models", {}).get("llm", {}).get("scene_max_tokens", 3500)
        response = self.llm.generate_json(prompt, system_prompt=system, temperature=0.2, max_tokens=max_t)

        try:
            data = json.loads(response)
        except Exception as e:
            logger.warning(f"StoryboardPlanner JSON parse failed: {e}")
            return {"state": current_state, "pages": []}

        if not isinstance(data, dict):
            logger.warning("StoryboardPlanner output is not a dictionary.")
            return {"state": current_state, "pages": []}

        state = data.get("state", current_state)
        pages_raw = data.get("pages", [])
        
        valid_pages = []
        seq = start_sequence
        page_num = start_page

        for p_raw in pages_raw:
            try:
                template = p_raw.get("layout_template")
                if template not in ["1_panel_splash", "3_panel_action", "4_panel_grid"]:
                    logger.warning(f"Invalid template {template}, defaulting to 4_panel_grid")
                    template = "4_panel_grid"
                    
                expected_panels = 4
                if template == "1_panel_splash": expected_panels = 1
                elif template == "3_panel_action": expected_panels = 3
                
                panels = p_raw.get("panels", [])
                # Force exact number of panels if LLM messes up
                if len(panels) < expected_panels:
                    # Pad
                    while len(panels) < expected_panels:
                        panels.append({"description": "continued action", "visual_tags": ["cinematic"]})
                elif len(panels) > expected_panels:
                    panels = panels[:expected_panels]
                    
                valid_panels = []
                for idx, panel_data in enumerate(panels):
                    desc = str(panel_data.get("description", "")).strip() or "scene"
                    panel_obj = {
                        "id": f"p{seq}",
                        "sequence": seq,
                        "description": desc,
                        "visual_tags": panel_data.get("visual_tags", []),
                        "characters": panel_data.get("characters", []),
                        "location": panel_data.get("location", state.get("current_location", "unknown")),
                        "chapter": chapter,
                        "panel_index": idx
                    }
                    valid_panels.append(panel_obj)
                    seq += 1
                
                valid_pages.append({
                    "id": f"page_{page_num:03d}",
                    "page_number": page_num,
                    "layout_template": template,
                    "reasoning": p_raw.get("reasoning", ""),
                    "panels": valid_panels
                })
                page_num += 1
            except Exception as e:
                logger.warning(f"Failed to validate page {p_raw}: {e}")
                continue

        return {"state": state, "pages": valid_pages}
