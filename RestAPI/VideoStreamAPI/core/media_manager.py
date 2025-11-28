import ffmpeg
from pathlib import Path
import logging
logger : logging.Logger = logging.getLogger("app")

from VideoStreamAPI.core.upload_manager import UploadManager
from VideoStreamAPI.core.video_manager import VideoManager


class MediaManager:

    def __init__(self, abs_video_dir = "", host = "127.0.0.1", port = 5000 ):
        self.video_dir = abs_video_dir
        self.output_dir = Path(abs_video_dir) / "videos"
        self.upload_dir = Path(abs_video_dir) / "uploads"

        self.uploader = UploadManager(self.upload_dir)
        self.video_manager = VideoManager(self.output_dir, self.upload_dir)

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

        self.host = host
        self.port = port


  

