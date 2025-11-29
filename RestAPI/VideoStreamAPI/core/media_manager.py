import ffmpeg
from pathlib import Path
import threading
from queue import Queue
from datetime import datetime
import logging
logger : logging.Logger = logging.getLogger("app")

from VideoStreamAPI.core.upload_manager import UploadManager
from VideoStreamAPI.core.video_manager import VideoManager


class MediaManager:

    def __init__(self, abs_video_dir = "", db = None):
        self.video_dir = abs_video_dir
        self.output_dir = Path(abs_video_dir) / "videos"
        self.upload_dir = Path(abs_video_dir) / "uploads"

        self.uploader = UploadManager(self.upload_dir)
        self.video_manager = VideoManager(self.output_dir, self.upload_dir)

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

        self.db = db
        self.queue = Queue()
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def AddTask(self, type, media_id, **kwargs ):
        creation_date = datetime.now().isoformat()        
        task_db = {
            "status": "pending",
            "task_type": type,
            "media_id": media_id,
            "error_message": "",
            "creation_date": creation_date,                        
        }
        task = task_db
        task['params'] = kwargs

        task_db = self.db.tasks.Create(task_db)
        if task_db is None:
            return task_db
        logger.info(f"Queuing Media task: {task_db}")
        task['task_id'] = task_db['id']
        self.queue.put(task)
        return task_db
  

    def _worker(self):

        while True:
            task = self.queue.get()
            task_db = self.db.tasks.Get(task["task_id"])
            task_db["status"] = "running"
            self.db.tasks.Update(task_db)

            if task['task_type'] == "hls_build":
                logger.info(f"Starting task: {task_db}")
                media = self.db.media.Get(task["media_id"])
                file_name =  self.uploader.GetFileName(media['hash'], media['mimetype'])
                meta_data = self.video_manager.LoadData(file_name)

                if self.video_manager.DirExists(media['hash']):
                    self.video_manager.DirRemove(media['hash'])

                res = self.video_manager.CreateHls(meta_data,media['hash'], **task['params'])
                if not res.get('build_status', False):
                    logger.warning(f"Task failed: {task_db}")
                    task_db['status'] = "error"
                    task_db['error_message'] = "failed to create hls"
                    self.db.tasks.Update(task_db)
                else:
                    logger.info("Task completed: {task_db}")
                    task_db['status'] = "done"
                    self.db.tasks.Update(task_db)
            else:
                logger.warning(f"Invalid task type. Skipping")
                task_db["status"] = "error"
                task_db['error_message'] = f"Invalid task type"
                self.db.tasks.Update(task_db)

