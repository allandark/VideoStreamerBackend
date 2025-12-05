import ffmpeg
from pathlib import Path
import threading
from queue import Queue
from datetime import datetime
import logging
logger : logging.Logger = logging.getLogger("app")

from VideoStreamAPI.core.upload_manager import UploadManager
from VideoStreamAPI.core.video_manager import VideoManager

class TaskStatus:
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"

class TaskType:
    HLS_BUILD = "hls_build"
    FILE_REASSEMBLY = "upload_chunked"

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
        if task_id is None:
            creation_date = datetime.now().isoformat()
            task_data = {
                "status": TaskStatus.PENDING,
                "task_type": type,
                "media_id": media_id,
                "error_message": "",
                "creation_date": creation_date,
                "params": kwargs
            }
            # TODO: check for correct params
            if type == TaskType.HLS_BUILD:
                if media_id == 0:
                    logger.warning(f"hls_build cannot have undefined media_id. Aborting task")
                    task_data["error_message"] = "hls_build cannot have undefined media_id"
                    task_data['status'] = TaskStatus.ERROR
                    queue_task = False
                
            elif type == TaskType.FILE_REASSEMBLY:
                if media_id == 0 and 'mimetype' in task_data['params']:
                    hash = task_data['params'].get('hash', "")
                    mimetype =  task_data['params']['mimetype']
                    if not self.uploader.FileExists(hash, mimetype):
                        # Create new media model
                        media = self.db.media.Create({
                            "name": task_data['params'].get('file_name', "DefaultMediaName"),
                            "hash": hash,
                            "mimetype" : mimetype
                        })
                        task_data['media_id'] = media['id']
                    else:
                        logger.error(f"Media file already exists: {self.uploader.GetFileName(hash, mimetype)}")
                        task_data['status'] = TaskStatus.ERROR
                        task_data['error_message'] = "Media file already exists"
                        task_data['media_id'] = None
                else:
                    logger.error(f"Failed to create media for task: {task_data}")
                    task_data['media_id'] = None


                if 'file_name' in task_data['params'] or\
                        'chunk_size' in task_data['params'] or\
                        'chunk_count' in task_data['params']:
                    task_data['params']['received_chunks'] = {}
                else:
                    task_data['status'] = TaskStatus.ERROR
                    task_data['error_message'] = "Wrong params provided. Task requires: \"file_name\", \"chunk_size\", \"chunk_count\""
                
            if task_data is None:
                logger.error(f"Failed to create media task")
                return None

            task = self.db.tasks.Create(task_data)
            logger.info(f"Created new Media task: {task}")
        else:
            task = self.db.tasks.Get(task_id)
            if task is None:
                return task
            task["params"].update(kwargs)
            self.db.tasks.Update(task)
            logger.info(f"Updated Media task: {task}")

        if queue_task:
            logger.debug(f"Queuing Media task: {task}")
            self.queue.put(task)
        
        return task
  

    def _worker(self):

        while True:
            task = self.queue.get()
            task_db = self.db.tasks.Get(task["id"])
            task_db["status"] = TaskStatus.RUNNING
            self.db.tasks.Update(task_db)

            if task['task_type'] == TaskType.HLS_BUILD:
                logger.info(f"Starting task: {task_db}")
                media = self.db.media.Get(task["media_id"])
                file_name =  self.uploader.GetFileName(media['hash'], media['mimetype'])
                meta_data = self.video_manager.LoadData(file_name)

                if self.video_manager.DirExists(media['hash']):
                    self.video_manager.DirRemove(media['hash'])

                res = self.video_manager.CreateHls(meta_data,media['hash'], **task['params'])
                if not res.get('build_status', False):
                    logger.warning(f"Task failed: {task_db}")
                    task_db['status'] = TaskStatus.ERROR
                    task_db['error_message'] = "failed to create hls"
                    self.db.tasks.Update(task_db)
                else:
                    logger.info(f"Task completed: {task_db}")
                    task_db['status'] = TaskStatus.DONE
                    self.db.tasks.Update(task_db)
            elif task['task_type'] == TaskType.FILE_REASSEMBLY:
                logger.info(f"Starting task: {task_db}")
                media = self.db.media.Get(task["media_id"])
                hash = self.uploader.ChunkAssemble(task["id"], media['mimetype'])
                if hash is None:
                    logger.error(f"failed to assemble file: {file_name}")
                    task_db['status'] = TaskStatus.ERROR
                else:
                    media['hash'] = hash
                    task_db['status'] = TaskStatus.DONE
                    self.db.media.Update(media)
                self.db.tasks.Update(task_db)
                
            else:
                logger.warning(f"Invalid task type. Skipping")
                task_db["status"] = TaskStatus.ERROR
                task_db['error_message'] = f"Invalid task type"
                self.db.tasks.Update(task_db)

