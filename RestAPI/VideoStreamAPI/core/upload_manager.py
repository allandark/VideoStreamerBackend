import hashlib
from pathlib import Path
import os
import logging
from io import BytesIO
from typing import Optional
from werkzeug.datastructures import FileStorage
logger : logging.Logger = logging.getLogger("app")


class UploadManager:
    """ Class providing upload utilities and file handling
    """

    def __init__(self, upload_dir : Path, temp_dir: Path):
        """

        Args:
            upload_dir (Path): Path to upload directory
            temp_dir (Path): Path to temp directory
        """
        self.upload_dir = upload_dir
        self.temp_dir = temp_dir

        self.stored_files = {}


    def ChunkCreateDir(self, task_id: int):
        """ Create a temp dir for chunked uploads

        Args:
            task_id (int): uploading task id

        Returns:
            Path: Path to directory
        """
        path = self.temp_dir / str(task_id)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def ChunkSave(self, task_id: int, chunk_index: int,  file : FileStorage):
        """ Save chunk/segment of file

        Args:
            task_id (int): uploading task id
            chunk_index (int): chunk/segment number
            file (FileStorage): file to store

        Returns:
            Path|None: path to the saved file or None if failed
        """
        try:
            task_dir = self.ChunkCreateDir(task_id)
            chunk_path = task_dir / f"{chunk_index:06d}.part"
            file.save(chunk_path)
            logger.debug(f"File saved: {chunk_path}")
            return chunk_path
        except Exception as e:
            logger.error(f"Failed to save chunk file: {e}")
            return None

    def ChunkAssemble(self, task_id: int, mimetype : str ,output_file: Optional[str] = None):
        """ Assemble chunks to complete file. Calculate hash of blob. Move file to upload folder.

        Args:
            task_id (int): uploading task id
            mimetype (str): file type
            output_file (Optional[str], optional): Output file path. Defaults to None.

        Returns:
            str|None: file hash or None if failed
        """
        task_dir = self.temp_dir / str(task_id)
        if not task_dir.exists():
            return None
        
        if output_file is None:            
            output_file = task_dir / f"{task_id}_assembled"
            logger.warning(f"No output file provided using defualt: {output_file}")
        else:
            output_file = Path(output_file)

        chunk_files = sorted(task_dir.glob("*.part"))
        try:
            with open(output_file, "wb") as out_f:
                for chunk_file in chunk_files:
                    with open(chunk_file, "rb") as cf:
                        out_f.write(cf.read())                
            logger.info(f"Chunk files assembled: {output_file}")

            with open(output_file, "rb") as in_f:
                file_hash = self.GetHash(in_f)

            
            path = self.upload_dir / self.GetFileName(file_hash, mimetype)            
            logger.debug(f"Renameing file: {path}")
            os.rename(output_file, path)


            logger.debug(f"Deleteing chunk files")
            for chunk_file in chunk_files:
                chunk_file.unlink()
            return file_hash
        except Exception as e:
            logger.error(f"Failed to assemble files. Error: {e}")
            return None

    def AllowedMimetype(self, mimetype: str):
        """ _(Unused)_ returns true if mimetype is supported

        Args:
            mimetype (str): file type

        Returns:
            bool: true if type is supported
        """
        allowed_types = ['png', 'mp4', 'svg']
        return mimetype in allowed_types

    def GetDir(self):
        """ Returns upload directory

        Returns:
            Path: upload directory
        """
        return self.upload_dir

    def GetHash(self, file: BytesIO, chunk_size: int = 1024*1024):
        """ Calculates sh256 hash on file stream chunked.

        Args:
            file (BytesIO): file stream
            chunk_size (int, optional): chunk size. Defaults to 1024*1024.

        Returns:
            str|None: file hash or none
        """
        try:
            h = hashlib.new('sha256')
            while True:
                data = file.read(chunk_size)
                if not data:
                    break
                h.update(data)
            hash = h.hexdigest()    
            file.seek(0)        
            return hash
        except Exception as e:
            logger.warning(f"Error when generating hash: {e}")
            return None

    def GetFileExt(self, mimetype : str):
        """ Returns file extention from mimetype

        Args:
            mimetype (str): file type

        Returns:
            str: extention
        """
        file_ext = mimetype.split('/')[1]
        return  f"{file_ext}"


    def GetFileUrl(self, hash : str, mimetype: str):
        """ Returns absolute path to file

        Args:
            hash (str): file hash
            mimetype (str): file type

        Returns:
            Path: path to file
        """
        file_path = self.upload_dir / self.GetFileName(hash, mimetype)
        return str(file_path)

    def GetFileName(self , hash: str, mimetype: str):
        """ Builds filename from hash and type.

        Args:
            hash (str): file hash
            mimetype (str): file type

        Returns:
            str: file name
        """
        return str(f"{hash}.{self.GetFileExt(mimetype)}")


    def FileExists(self, hash: str, mimetype: str):
        """ Checks whether the file exists

        Args:
            hash (str): file hash
            mimetype (str): file type

        Returns:
            bool: true if file exists
        """
        file_path = self.upload_dir / self.GetFileName(hash, mimetype)
        return os.path.exists(file_path)

    def FileRemove(self, hash: str, mimetype: str):
        """ Remove file

        Args:
            hash (str): file hash
            mimetype (str): mimetype

        Returns:
            bool: True if file is removed
        """
        try:
            file_path = self.upload_dir / self.GetFileName(hash, mimetype)
            os.remove(file_path)
            logger.info(f"File deleted successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to delete: {e}")
            return False

    def FileSave(self, file : FileStorage, filename : str):
        """ Save file to upload directory

        Args:
            file (FileStorage): file to save
            filename (str): file name

        Returns:
            dict: file data: hash, file_name and mimetype
        """
        try:            

            file_hash = self.GetHash(file.stream)
            mimetype = file.mimetype
            file_path = self.upload_dir / self.GetFileName(hash, mimetype)
            
            file.save(dst=file_path)
            res = {"hash": file_hash ,"file_name": filename, "type": mimetype}
            return res

        except Exception as e:
            logger.error(f"Failed to save file \"{filename}\". Error: {e}")
            return None
        