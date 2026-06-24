"""
Storyboard Planner — Novel Video Factory v5
Extracts visual narrative beats from text chunks to generate a flat storyboard sequence.
Maintains continuity state across chunks.
"""
import json
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class StoryboardPlanner:
    """
    Breaks narrative blocks into cinematic visual beats.
    Maintains environment state (location, characters, time, weather) across blocks.
    """
    def __init__(self, llm_adapter, config: dict = None):
        self.llm = llm_adapter
        self.config = config or {}

        self.VALID_BEATS = {
            "environment", "action", "reaction", "emotion",
            "dialogue", "object_focus", "reveal", "combat", "transition"
        }
        self.VALID_SHOTS = {
            "establishing_shot", "wide_shot", "medium_shot",
            "close_up", "extreme_close_up", "over_shoulder"
        }

    def plan_panels(self, text_chunk: str, current_state: dict, chapter: int = 1, start_sequence: int = 1) -> dict:
        """
        Convert a text chunk into a list of visual panels.
        Returns a dict containing 'state' and 'panels'.
        """
        system = (
            "STORYBOARDPLANNER MASTER DIRECTIVE\n\n"
            "You are a professional Korean Manhwa webtoon artist.\n"
            "Your goal is to convert prose into a highly dense, dynamic sequence of panels.\n\n"
            "CORE PRINCIPLE:\n"
            "Create a NEW panel whenever:\n"
            "- dialogue speaker changes\n"
            "- significant action occurs\n"
            "- emotion changes\n"
            "- location changes\n"
            "- camera angle changes\n"
            "A fast-paced TikTok/YouTube manhwa video requires an image change every 3-5 seconds.\n"
            "DO NOT set merge_with_previous to true unless absolutely nothing has changed.\n\n"
            "VISUAL TAGS RULE:\n"
            "Extract visual details of the character, action, emotion, background, and environment.\n"
            "Keep the actual prose or dialogue snippet in 'description'.\n"
            "Put all visual elements in the 'visual_tags' list.\n\n"
            "NO MARKDOWN: Output ONLY valid JSON.\n\n"
            "JSON SCHEMA:\n"
            "{\n"
            '  "state": {\n'
            '    "current_location": "",\n'
            '    "time_of_day": "",\n'
            '    "weather": "",\n'
            '    "active_characters": []\n'
            "  },\n"
            '  "panels": [\n'
            "    {\n"
            '      "beat_type": "dialogue",\n'
            '      "shot_type": "close_up",\n'
            '      "importance": 8,\n'
            '      "location": "Riverbank",\n'
            '      "focus_character": "Arthur",\n'
            '      "characters": ["Arthur"],\n'
            '      "emotion": "angry",\n'
            '      "visual_tags": ["young man", "glaring angrily", "gritting teeth", "riverbank", "sunset"],\n'
            '      "description": "Arthur glares angrily as he speaks."\n'
            "    }\n"
            "  ]\n"
            "}"
        )

        payload = {
            "provided_state": current_state,
            "narrative_block": text_chunk
        }
        prompt = json.dumps(payload, indent=2)

        max_t = self.config.get("models", {}).get("llm", {}).get("scene_max_tokens", 3500)
        response = self.llm.generate_json(prompt, system_prompt=system, temperature=0.2, max_tokens=max_t)

        try:
            data = json.loads(response)
        except Exception as e:
            logger.warning(f"StoryboardPlanner JSON parse failed: {e}")
            return {"state": current_state, "panels": []}

        if not isinstance(data, dict):
            logger.warning("StoryboardPlanner output is not a dictionary.")
            return {"state": current_state, "panels": []}

        state = data.get("state", current_state)
        panels_raw = data.get("panels", [])
        
        if not isinstance(panels_raw, list):
            logger.warning("StoryboardPlanner 'panels' is not a list.")
            panels_raw = []

        valid_panels = []
        seq = start_sequence

        for p in panels_raw:
            try:
                bt = str(p.get("beat_type", "action")).lower()
                st = str(p.get("shot_type", "medium_shot")).lower()
                imp = int(p.get("importance", 5))
                desc = str(p.get("description", "")).strip()

                if bt not in self.VALID_BEATS:
                    bt = "action"
                if st not in self.VALID_SHOTS:
                    st = "medium_shot"
                if not (1 <= imp <= 10):
                    imp = max(1, min(10, imp))
                
                if not desc:
                    continue  # skip empty descriptions

                import re
                internal_pattern = r"\b(realize|realizes|realization|remembers|remembered|memory|memories|thinks|thought|understands|understood|knows|learned|learns|transmigration|rebirth|past life|reflection|reflecting)\b"
                if re.search(internal_pattern, desc.lower()):
                    imp = min(imp, 4)
                    if bt in ["action", "combat", "reveal", "environment", "object_focus", "transition"]:
                        bt = "emotion"

                merge = False
                if imp <= 4:
                    merge = True
                elif bt == "transition":
                    merge = True
                elif bt == "dialogue" and imp < 7:
                    merge = True
                elif bt == "reaction" and imp < 7:
                    merge = True
                elif bt == "emotion" and imp < 8:
                    merge = True

                raw_loc = str(p.get("location", ""))
                if not raw_loc or raw_loc.lower() in ["same", "same as previous", "current location", "unknown"]:
                    raw_loc = state.get("current_location", "")

                fc_raw = str(p.get("focus_character", "")).strip()
                if fc_raw.lower() in ["none", "null", ""]:
                    fc = None
                else:
                    fc = fc_raw.split(",")[0].strip()

                panel = {
                    "id": f"p{seq}",
                    "sequence": seq,
                    "beat_type": bt,
                    "shot_type": st,
                    "importance": imp,
                    "merge_with_previous": merge,
                    "location": raw_loc,
                    "focus_character": fc,
                    "characters": p.get("characters", []),
                    "emotion": str(p.get("emotion", "")).strip(),
                    "visual_tags": p.get("visual_tags", []),
                    "description": desc,
                    "chapter": chapter
                }
                
                valid_panels.append(panel)
                seq += 1

            except Exception as e:
                logger.warning(f"Failed to validate panel {p}: {e}")
                continue

        # Post-processing pass: merge consecutive panels with same location and characters
        if valid_panels:
            last_unmerged_idx = 0
            for i in range(1, len(valid_panels)):
                curr = valid_panels[i]
                if curr["merge_with_previous"]:
                    continue
                    
                prev = valid_panels[last_unmerged_idx]
                
                same_loc = (curr["location"] == prev["location"])
                
                curr_chars = set(curr.get("characters", []))
                prev_chars = set(prev.get("characters", []))
                if curr_chars and prev_chars:
                    overlap = len(curr_chars.intersection(prev_chars)) / max(len(curr_chars), len(prev_chars))
                    same_chars = overlap >= 0.5 or curr_chars.issubset(prev_chars) or prev_chars.issubset(curr_chars)
                else:
                    same_chars = (curr_chars == prev_chars)
                
                is_env_change = curr["beat_type"] in ["reveal", "combat"] or (curr["beat_type"] == "action" and curr["importance"] >= 8)
                
                if same_loc and same_chars and not is_env_change:
                    curr["merge_with_previous"] = True
                else:
                    last_unmerged_idx = i

        return {"state": state, "panels": valid_panels}
