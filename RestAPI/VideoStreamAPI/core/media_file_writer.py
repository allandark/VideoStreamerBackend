import logging
logger : logging.Logger = logging.getLogger("app")

import os
import ffmpeg
from pathlib import Path
import subprocess
import shutil


class MediaManager:

    def __init__(self, abs_video_dir = "", host = "127.0.0.1", port = 5000 ):
        self.video_dir = abs_video_dir
        self.output_dir = Path(abs_video_dir) / "videos"
        self.upload_dir = Path(abs_video_dir) / "uploads"

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

        self.host = host
        self.port = port


    def video_get_metadata(self, input_file: str):
        input_path = self.upload_dir / input_file
        try:
            metadata = ffmpeg.probe(input_path)
            logger.debug(f"Metadata found")
            return metadata
        except Exception as e:
            logger.error(f"Metadata error: {e}")
            return None

    def video_generate_hls_variants(self, video_name: str):

        variants = [
            {"name": "240p", "width": 426, "height": 240, "bandwidth": 400_000},
            {"name": "480p", "width": 854, "height": 480, "bandwidth": 800_000},
            {"name": "720p", "width": 1280, "height": 720, "bandwidth": 1_500_000},
            {"name": "1080p", "width": 1920, "height": 1080, "bandwidth": 3_000_000},
        ]
        input_path = self.upload_dir / f"{video_name}.mp4"
        output_path = self.output_dir / video_name
        output_path.mkdir(parents=True, exist_ok=True)

        try:
            for variant in variants:
                res = self.video_generate_hls(
                    input_file=input_path,
                    output_path=output_path,
                    variant_name=variant["name"],
                    video_name=video_name,
                    host=self.host,
                    port=self.port,
                    width=variant["width"],
                    height=variant["height"])
                
                if not res:
                    logger.warning(f"Failed to generate hls for: {variant["name"]}")

            # Create master playlist
            master_playlist = output_path / "master.m3u8"
            with open(master_playlist, "w") as f:
                f.write("#EXTM3U\n#EXT-X-VERSION:3\n")
                for variant in variants:
                    f.write(f"#EXT-X-STREAM-INF:BANDWIDTH={variant['bandwidth']},RESOLUTION={variant['width']}x{variant['height']}\n")
                    f.write(f"{video_name}/{variant['name']}.m3u8\n")

                logger.info(f"Playlist file created: {master_playlist}")
            return True
        except Exception as e:
            logger.error(f"Error converting mp4 to hls format")
            return False


    def video_generate_hls(self,
            input_file: str,
            output_path: Path,
            variant_name: str,
            video_name : str,
            host: str,
            port: int,
            width: int,
            height: int):
        """
        Converts an MP4 file into HLS format using ffmpeg-python.
        """
        # Build output paths
        playlist_path = output_path / f"{variant_name}.m3u8"
        segment_pattern = output_path / f"{variant_name}_%d.ts"

        try:
            (
                ffmpeg
                .input(input_file)
                .output(
                    str(playlist_path),
                    codec="copy",
                    start_number=0,
                    hls_time=10,
                    hls_list_size=0,
                    hls_segment_filename=str(segment_pattern),
                    hls_base_url=f"http://{host}:{port}/api/video/chunk/{video_name}/",
                    format="hls"
                )
                .run(capture_stdout=True, capture_stderr=True)
            )
            return True

        except ffmpeg.Error as e:            
            logger.error(f"ffmpeg error: {e.stderr.decode('utf-8')}")
            return False
        except Exception as e:
            logger.error(f"{e}")
 


    def video_get_file(self, video_dir,  file = "master.m3u8"):
        return self.output_dir / video_dir / file

    def video_get_all(self):
        video_names = []
        for entry in os.listdir(self.output_dir):
            video_names.append({"name": entry, "type":".m3u8"})
        return video_names

    def video_file_exists(self, video_dir , file = "master.m3u8"):
        url = self.output_dir / video_dir / file
        return os.path.exists(url)

    def video_remove(self, video_dir):
        try:
            shutil.rmtree(self.output_dir / video_dir)      
            logger.info(f"HLS files deleted successfully")      
            return True
        except Exception as e: 
            logger.error(f"Failed to delete HLS files")
            return False      


    def upload_get_all(self):
        upload_dicts =[]
        for entry in os.listdir(self.upload_dir):
            ls = entry.split(".")
            upload_dicts.append( {"name": ls[0], "type": ls[1]})
        return upload_dicts
    
    def upload_get_file(self, video_dir):
        return self.upload_dir / f"{video_dir}.mp4"

    def upload_file_exists(self, video_dir ):
        url = self.upload_dir / f"{video_dir}.mp4"
        return os.path.exists(url)

    def upload_remove(self, video_dir):
        try:
            path = self.upload_dir / f"{video_dir}.mp4"
            os.remove(path)
            logger.info(f"File deleted successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to delete: {e}")
            return False

    def upload_save(self, file, filename):
        try:                 
            save_path = self.upload_dir / f"{filename}.mp4"
            file.save(save_path)
            logger.info(f"File added to upload: {save_path}")
            return True
        except Exception as e:
            logger.warning(f"File failed to be added: {e}")
            return False
 
