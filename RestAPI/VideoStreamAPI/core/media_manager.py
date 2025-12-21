import ffmpeg
from pathlib import Path
import threading
from queue import Queue

import logging
logger : logging.Logger = logging.getLogger("app")

from VideoStreamAPI.core.media_task import TaskStatus, ITask
from VideoStreamAPI.core.upload_manager import UploadManager
from VideoStreamAPI.core.video_manager import VideoManager



class MediaManager:

    def __init__(self, abs_video_dir = "", db = None):
        self.video_dir = abs_video_dir
        self.output_dir = Path(abs_video_dir) / "videos"
        self.upload_dir = Path(abs_video_dir) / "uploads"
        self.temp_dir = self.upload_dir / "tmp"

        self.uploader = UploadManager(self.upload_dir, self.temp_dir)
        self.video_manager = VideoManager(self.output_dir, self.upload_dir)

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        

        self.db = db
        self.queue = Queue()
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def AddOrUpdateTask(self, type, media_id, task_id=None, queue_task=True, **kwargs ):
        task = ITask.CreateTask(
            type = type,
            media_id = media_id, 
            params = kwargs,
            db = self.db,
            video_manager = self.video_manager,
            uploader = self.uploader,
            task_id = task_id
        )  
        if task is None:
            logger.error(f"Failed to  create task: {type}")

        if task_id is None:
            logger.debug(f"starting task: {task_id}")
            if not task.Start():                    
                queue_task = False
                
            if task is not None and task.status == TaskStatus.ERROR:
                logger.error(f"Failed to create media task")
                return None     
        else:   
            task.Update(params = kwargs)

        if queue_task:
            logger.debug(f"Queuing Media task: {task}")            
            self.queue.put(task)
        
        return task.data
  

    def _worker(self):

        while True:
            task = self.queue.get()
            task.Execute()


