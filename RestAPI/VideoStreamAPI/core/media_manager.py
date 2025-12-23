from VideoStreamAPI.db.db_context import DatabaseContext
from VideoStreamAPI.core.video_manager import VideoManager
from VideoStreamAPI.core.upload_manager import UploadManager
from VideoStreamAPI.core.media_task import TaskStatus, ITask, TaskType
from pathlib import Path
import threading
from threading import Thread
from queue import Queue

import logging
logger: logging.Logger = logging.getLogger("app")


class MediaManager:

    def __init__(self, abs_video_dir: str = "", db: DatabaseContext | None = None):
        """ _summary_\n
        Manager class for providing media utilities for saving, deleting and synchronizing
        media files. It offloads computation intensive task to another thread.

        Args:
            abs_video_dir (str, optional): _description_. Defaults to "".
            db (DatabaseContext | None, optional): _description_. Defaults to None.
        """
        self.video_dir: str = abs_video_dir
        self.output_dir: Path = Path(abs_video_dir) / "videos"
        self.upload_dir: Path = Path(abs_video_dir) / "uploads"
        self.temp_dir: Path = self.upload_dir / "tmp"

        self.uploader: UploadManager = UploadManager(
            self.upload_dir, self.temp_dir)
        self.video_manager: VideoManager = VideoManager(
            self.output_dir, self.upload_dir)

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        self.db: DatabaseContext = db
        self.queue: Queue = Queue()
        self.thread: Thread = threading.Thread(
            target=self._worker, daemon=True)
        self.thread.start()

    def AddOrUpdateTask(self, type: TaskType, media_id: int, task_id: int | None = None, queue_task: bool = True, **kwargs):
        """ _summary_\n
        Creates a new task or updates an existing task.
        Args:
            type (TaskType): _description_ type of media task
            media_id (int): _description_ id of media
            task_id (int | None, optional): _description_. Defaults to None (used for update task).
            queue_task (bool, optional): _description_. Defaults to True (queue task to process on worker thread).

        Returns:
            _type_: _description_
        """
        task = ITask.CreateTask(
            type=type,
            media_id=media_id,
            params=kwargs,
            db=self.db,
            video_manager=self.video_manager,
            uploader=self.uploader,
            task_id=task_id
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
            task.Update(params=kwargs)

        if queue_task:
            logger.debug(f"Queuing Media task: {task}")
            self.queue.put(task)

        return task.data

    def _worker(self):

        while True:
            task = self.queue.get()
            task.Execute()
