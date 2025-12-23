from VideoStreamAPI.db.db_context import DatabaseContext
from VideoStreamAPI.core.upload_manager import UploadManager
from VideoStreamAPI.core.video_manager import VideoManager
import abc
from datetime import datetime
import logging
logger: logging.Logger = logging.getLogger("app")


class TaskStatus:
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"


class TaskType:
    HLS_BUILD = "hls_build"
    FILE_REASSEMBLY = "upload_chunked"


class ITask(metaclass=abc.ABCMeta):
    """ _summary_\n
    Interface for media tasks ensuring common class pattern
    """

    INVALID_TASK_ID = -1

    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'Start') and callable(subclass.Start) and
                hasattr(subclass, 'Update') and callable(subclass.Update) and
                hasattr(subclass, 'Execute') and callable(subclass.Execute) and
                hasattr(subclass, 'type') and hasattr(subclass, 'status') or
                NotImplemented)

    @abc.abstractmethod
    def Start(self, **kvargs):
        raise NotImplemented

    @abc.abstractmethod
    def Update(self):
        raise NotImplemented

    @abc.abstractmethod
    def Execute(self):
        raise NotImplemented

    def CreateTask(type: TaskType, **kwargs):
        """ _summary_\n
        Static method for instantiating task object
        Args:
            type (TaskType): Task type 

        Returns:
            (ITask|None): Task handle or None
        """
        match type:
            case TaskType.HLS_BUILD:
                return HLSTask(media_id=kwargs.get('media_id'),
                               params=kwargs.get('params'),
                               db=kwargs.get('db'),
                               video_manager=kwargs.get('video_manager'),
                               uploader=kwargs.get('uploader'),
                               task_id=kwargs.get('task_id'))

            case TaskType.FILE_REASSEMBLY:
                return FileReassemblyTask(media_id=kwargs.get('media_id'),
                                          params=kwargs.get('params'),
                                          db=kwargs.get('db'),
                                          video_manager=kwargs.get(
                                              'video_manager'),
                                          uploader=kwargs.get('uploader'),
                                          task_id=kwargs.get('task_id'))
            case _:
                return None


class HLSTask(ITask):
    """ Implementation of HLS Task for building hls files and other ffmpeg related operations
    """

    def __init__(self, **kwargs):
        """ _summary_\n
        Initializes the HLS task object.
        Args:
          db (DatabaseContext): Reference to db context
          video_manager (VideoManager): Reference to video manager
          uploader (UploadManager): Reference to upload manager
          task_id (int): task db id
          media_id (int): media db id
          params (dict): params for hls builder
        """
        super().__init__()
        self.db: DatabaseContext | None = kwargs.get("db", None)
        self.vm: VideoManager | None = kwargs.get('video_manager', None)
        self.up: UploadManager | None = kwargs.get('uploader', None)
        task_id: int | None = kwargs.get('task_id', None)
        if task_id is None:
            self.id = self.INVALID_TASK_ID
            self.type = TaskType.HLS_BUILD
            self.status = TaskStatus.PENDING
            creation_date = datetime.now().isoformat()
            self.data = {
                "status": self.status,
                "task_type": self.type,
                "media_id": kwargs.get("media_id", 0),
                "error_message": "",
                "creation_date": creation_date,
                "params": kwargs.get("params", "")
            }
        else:
            self.data: dict = self.db.tasks.get(task_id)
            self.id: int = task_id
            self.type: TaskType = TaskType.FILE_REASSEMBLY
            self.status: TaskStatus = self.data['status']

    def Start(self):
        """ _summary_\n
        Creates a media task on database
        Returns:
            bool: true if task is created
        """
        if self.data['media_id'] == 0:
            msg = f"hls_build cannot have undefined media_id. Aborting task"
            self._error(msg)  # TODO: task is not created yet on db
            return False

        self.data = self.db.tasks.Create(self.data)
        self.id = self.data["id"]
        logger.info(f"Created new Media task: {self.data}")
        return True

    def Update(self, **kwargs):
        """ _summary_\n
        Update existing media task with kwargs
        Args:
            task_id (int): task id
            params (dict): params to update
        Returns:
            (dict|None): updated task model
        """
        self.data = self.db.tasks.Get(kwargs.get('task_id'))
        if self.data is None:
            return None
        self.data['params'].update(kwargs.get("param"))
        self.data = self.db.tasks.Update(self.data)
        logger.info(f"Updated Media task: {self.data}")
        return self.data

    def Execute(self):
        """ _summary_\n
        Executes the hls build task with to be offloaded to worker thread
        """
        self.data = self.db.tasks.Get(self.id)
        self.status = TaskStatus.RUNNING
        self.data["status"] = self.status
        self.db.tasks.Update(self.data)

        logger.info(f"Executing task: {self.data}")
        media = self.db.media.Get(self.data["media_id"])

        file_name = self.up.GetFileName(media['hash'], media['mimetype'])
        try:
            meta_data = self.vm.LoadData(file_name)
        except Exception as e:
            msg = f"Could not load media file: \"{file_name}\". Error: {e}"
            meta_data = None
            self._error(msg)
        if meta_data is None:
            return

        if self.vm.DirExists(media['hash']):
            self.vm.DirRemove(media['hash'])

        res = self.vm.CreateHls(
            meta_data, media['hash'], **self.data['params'])

        if not res.get('build_status', False):
            self._error("Failed to complete hls build task")
        else:

            if self.data['params'].get("build_video", False):
                media['video_tracks'] = self.data['params'].get(
                    'video_tracks', [])
                media['master'] = True

            if self.data['params'].get("build_audio", False):
                media['audio_tracks'] = self.data['params'].get(
                    'audio_tracks', [])
                media['master'] = True

            if self.data['params'].get("build_subtitle", False):
                media['subtitle_tracks'] = self.data['params'].get(
                    'subtitle_tracks', [])
                media['master'] = True

            if self.data['params'].get("build_thumbnail", False):
                media['thumbnail'] = True

            self.db.media.Update(media)
            logger.info(f"Task completed: {self.data}")
            self.data['status'] = TaskStatus.DONE
            self.status = TaskStatus.DONE
            self.db.tasks.Update(self.data)

    def _error(self, msg: str):
        logger.error(msg)
        self.data['error_message'] = msg
        self.status = TaskStatus.ERROR
        self.data['status'] = self.status
        self.data = self.db.tasks.Update(self.data)


class FileReassemblyTask(ITask):
    """ Implementation of task for chunked file upload
    """

    def __init__(self,  **kwargs):
        """ _summary_\n
        Initialize FileReassemblyTask.
        Args:
          db (DatabaseContext):
          video_manager (VideoManager):
          uploader (UploadManager): 
          task_id (int): 
          media_id (int): 
          params (dict):
        """
        super().__init__()
        self.db: DatabaseContext | None = kwargs.get("db", None)
        self.vm: VideoManager | None = kwargs.get('video_manager', None)
        self.up: UploadManager | None = kwargs.get('uploader', None)

        task_id = kwargs.get('task_id', None)
        if task_id is None:
            self.id = self.INVALID_TASK_ID
            self.status = TaskStatus.PENDING
            creation_date = datetime.now().isoformat()
            self.type = TaskType.FILE_REASSEMBLY
            self.data = {
                "status": self.status,
                "task_type": self.type,
                "media_id": kwargs.get("media_id", 0),
                "error_message": "",
                "creation_date": creation_date,
                "params": kwargs.get("params", "")
            }
        else:
            self.data = self.db.tasks.Get(task_id)
            self.id = task_id
            self.type = TaskType.FILE_REASSEMBLY
            self.status = self.data['status']

    def Start(self):
        """ _summary_\n
        Start chunked file upload task and creates database entry
        Returns:
            bool: true if task created successfully
        """
        if self.data['media_id'] == 0 and 'mimetype' in self.data['params']:
            hash = self.data['params'].get('hash', "")
            mimetype = self.data['params']['mimetype']
            if not self.up.FileExists(hash, mimetype):
                # Create new media model
                media = self.db.media.Create({
                    "name": self.data['params'].get('file_name', "DefaultMediaName"),
                    "hash": hash,
                    "mimetype": mimetype
                })

                self.data['media_id'] = media['id']
                logger.debug(f"Media created: {self.data['media_id']}")
            else:
                self.data['media_id'] = None
                self._error(
                    f"Media file already exists: {self.up.GetFileName(hash, mimetype)}")
                return False

        else:
            self.data['media_id'] = None
            self._error(f"Failed to create media for task: {self.data}")
            return False

        if 'file_name' in self.data['params'] or\
            'chunk_size' in self.data['params'] or\
                'chunk_count' in self.data['params']:
            self.data['params']['received_chunks'] = {}
        else:
            self._error(
                "Wrong params provided. Task requires: \"file_name\", \"chunk_size\", \"chunk_count\"")
            return False
        self.data = self.db.tasks.Create(self.data)
        self.id = self.data["id"]
        logger.info(f"Created new Media task: {self.data}")
        return True

    def Update(self, **kwargs):
        """ _summary_\n
        Update running file upload task
        Returns:
            (dict): task model
        """
        self.data['params'].update(kwargs.get("params"))
        self.data = self.db.tasks.Update(self.data)
        logger.info(f"Updated Media task: {self.data}")
        return self.data

    def Execute(self):
        """ _summary_\n
        Executes task on worker thread. Assembles file segments and updates database
        """
        self.data = self.db.tasks.Get(self.id)
        self.status = TaskStatus.RUNNING
        self.data['status'] = self.status
        self.db.tasks.Update(self.data)
        logger.info(f"Starting task: {self.data}")
        media = self.db.media.Get(self.data["media_id"])
        hash = self.up.ChunkAssemble(self.data["id"], media['mimetype'])
        if hash is None:
            self._error(f"failed to assemble file: {self.data['file_name']}")

        else:
            media['hash'] = hash
            self.status = TaskStatus.DONE
            self.data['status'] = self.status
            self.db.media.Update(media)
            self.db.tasks.Update(self.data)

    def _error(self, msg: str):
        logger.error(msg)
        self.data['error_message'] = msg
        self.status = TaskStatus.ERROR
        self.data['status'] = self.status
        self.data = self.db.tasks.Update(self.data)
