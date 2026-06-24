import os
import subprocess
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class VideoRenderer:
    """
    Video Renderer — Novel Video Factory v5
    Assembles static panel pages into a final video.
    Completely replaces Ken Burns with lightning-fast static FFmpeg concat.
    """
    def __init__(self, project_dir: str, config: dict = None):
        self.project_dir = project_dir
        self.output_dir = os.path.join(project_dir, "output")
        self.videos_dir = os.path.join(self.output_dir, "videos")
        self.pages_dir = os.path.join(self.output_dir, "pages")
        self.audio_dir = os.path.join(self.output_dir, "audio")
        self.temp_dir = os.path.join(self.output_dir, "temp")
        
        self.storyboard_path = os.path.join(self.output_dir, "storyboard.json")
        self.final_video_path = os.path.join(self.videos_dir, "final_video.mp4")

        os.makedirs(self.videos_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)
        logger.info(f"VideoRenderer: Starting assembly...")

    def render(self):
        import json
        if not os.path.exists(self.storyboard_path):
            logger.error("storyboard.json not found — cannot render video")
            return

        with open(self.storyboard_path, "r", encoding="utf-8") as f:
            all_pages = json.load(f)

        if not all_pages:
            logger.error("No pages found in storyboard.json.")
            return

        segment_paths = []

        for pg in all_pages:
            page_id = pg.get("id", f"page_{pg.get('page_number', 0):03d}")
            page_image_path = os.path.join(self.pages_dir, f"{page_id}.png")
            
            if not os.path.exists(page_image_path):
                logger.warning(f"Missing composite page: {page_image_path} — skipping")
                continue
                
            panels = pg.get("panels", [])
            audio_paths = []
            for p in panels:
                aud_path = os.path.join(self.audio_dir, f"{p['id']}.wav")
                if os.path.exists(aud_path):
                    audio_paths.append(aud_path)
            
            page_audio_path = os.path.join(self.temp_dir, f"{page_id}_audio.wav")
            
            # Combine audio
            if len(audio_paths) > 0:
                self.concatenate_audio(audio_paths, page_audio_path)
            else:
                logger.warning(f"No audio for {page_id}, using 3s silence.")
                # generate silence
                cmd_silence = [
                    "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
                    "-t", "3", page_audio_path
                ]
                subprocess.run(cmd_silence, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

            temp_output_path = os.path.join(self.temp_dir, f"{page_id}.mp4")
            logger.info(f"Rendering static segment for {page_id}...")
            self.render_page_segment(page_image_path, page_audio_path, temp_output_path)
            
            if os.path.exists(temp_output_path):
                segment_paths.append(temp_output_path)

        if not segment_paths:
            logger.error("No valid shots to render.")
            return

        logger.info(f"Assembling {len(segment_paths)} segments into final video...")
        self.assemble_final_video(segment_paths)
        
        # Generate SRT
        self.generate_srt(all_pages)

    def concatenate_audio(self, audio_paths: List[str], output_audio_path: str):
        """Stitches panel wav files into a single master page audio file via FFmpeg."""
        if len(audio_paths) == 1:
            import shutil
            shutil.copy(audio_paths[0], output_audio_path)
            return

        # Write file list for audio concat demuxer
        concat_file_path = os.path.join(self.temp_dir, "audio_concat.txt")
        with open(concat_file_path, "w", encoding="utf-8") as f:
            for path in audio_paths:
                absolute_path = os.path.abspath(path).replace("\\", "/")
                f.write(f"file '{absolute_path}'\n")

        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file_path,
            "-c", "copy",
            output_audio_path
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=False)
        # If copy fails due to mismatched formats, fallback to re-encoding
        if not os.path.exists(output_audio_path):
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_file_path,
                "-ar", "44100",
                "-ac", "2",
                output_audio_path
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True)

    def render_page_segment(self, page_image_path: str, page_audio_path: str, temp_output_path: str):
        """Renders a low-overhead static layout presentation mapped to audio length."""
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", page_image_path,
            "-i", page_audio_path,
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-pix_fmt", "yuv420p",
            "-shortest",
            temp_output_path
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True)

    def assemble_final_video(self, segment_paths: List[str], final_output_name: str = "final_video.mp4") -> str:
        """Assembles all temporary segments into a final sequence using demuxing text files."""
        concat_file_path = os.path.join(self.temp_dir, "video_concat.txt")
        
        with open(concat_file_path, "w", encoding="utf-8") as f:
            for path in segment_paths:
                absolute_path = os.path.abspath(path).replace("\\", "/")
                f.write(f"file '{absolute_path}'\n")
                
        final_video_path = os.path.join(self.videos_dir, final_output_name)
        
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file_path,
            "-c", "copy", # No re-encoding needed; ultra-fast performance
            final_video_path
        ]
        
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True)
        logger.info(f"✓ Video saved: {final_video_path}")
        return final_video_path

    def generate_srt(self, all_pages: List[dict]):
        srt_path = os.path.join(self.videos_dir, "subtitles.srt")
        def format_time(seconds):
            hrs = int(seconds // 3600)
            mins = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            msecs = int((seconds % 1) * 1000)
            return f"{hrs:02d}:{mins:02d}:{secs:02d},{msecs:03d}"

        current_time = 0.0
        srt_index = 1
        
        try:
            with open(srt_path, "w", encoding="utf-8") as f:
                for pg in all_pages:
                    panels = pg.get("panels", [])
                    
                    for p in panels:
                        panel_id = p.get("id", "")
                        panel_audio_path = os.path.join(self.audio_dir, f"{panel_id}.wav")
                        panel_duration = 3.0
                        
                        if os.path.exists(panel_audio_path):
                            # fast duration check
                            cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", panel_audio_path]
                            res = subprocess.run(cmd, capture_output=True, text=True)
                            try:
                                panel_duration = float(res.stdout.strip())
                            except ValueError:
                                pass
                                
                        text = p.get("description", "").strip()
                        
                        if text:
                            start_str = format_time(current_time)
                            end_str = format_time(current_time + panel_duration)
                            f.write(f"{srt_index}\n{start_str} --> {end_str}\n{text}\n\n")
                            srt_index += 1
                            
                        current_time += panel_duration
                        
            logger.info("✓ SRT generated")
        except Exception as e:
            logger.error(f"Failed to generate SRT: {e}")
