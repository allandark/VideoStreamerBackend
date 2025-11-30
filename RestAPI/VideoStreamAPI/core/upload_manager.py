import hashlib
from pathlib import Path
import os
import logging
from typing import Optional
from werkzeug.datastructures import FileStorage
logger : logging.Logger = logging.getLogger("app")


class UploadManager:

    def __init__(self, upload_dir : Path, temp_dir: Path):
        self.upload_dir = upload_dir
        self.temp_dir = temp_dir

        self.stored_files = {}


    def ChunkCreateDir(self, task_id: int):
        path = self.temp_dir / str(task_id)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def ChunkSave(self, task_id: int, chunk_index: int,  file : FileStorage):
        try:
            task_dir = self.ChunkCreateDir(task_id)
            chunk_path = task_dir / f"{chunk_index:06d}.part"
            file.save(chunk_path)
            logger.debug(f"File saved: {chunk_path}")
            return chunk_path
        except Exception as e:
            logger.error(f"Failed to save chunk file: {e}")
            return None

    def ChunkAssemble(self, task_id: int, output_file: Optional[str] = None):
        task_dir = self.temp_dir / str(task_id)
        if not task_dir.exists():
            return None
        
        if output_file is None:            
            output_file = task_dir / f"{task_id}_assembled"
            logger.warning(f"No output file provided using defualt: {output_file}")
        else:
            output_file = Path(output_file)

        chunk_files = sorted(task_dir.glob("*.chunk"))
        try:
            with open(output_file, "wb") as out_f:
                for chunk_file in chunk_files:
                    with open(chunk_file, "rb") as cf:
                        out_f.write(cf.read())
            logger.info(f"Chunk files assembled: {output_file}")

            logger.debug(f"Deleteing chunk files")
            for chunk_file in chunk_files:
                chunk_file.unlink()
            return str(output_file)
        except Exception as e:
            logger.error(f"Failed to assemble files. Error: {e}")
            return None

    def AllowedMimetype(self, mimetype: str):
        allowed_types = ['png', 'mp4', 'svg']
        return mimetype in allowed_types

    def GetDir(self):
        return self.upload_dir

    def GetHash(self, file: FileStorage, chunk_size = 1024*1024):
        try:
            h = hashlib.new('sha256')
            while True:
                data = file.stream.read(chunk_size)
                if not data:
                    break
                h.update(data)
            hash = h.hexdigest()    
            file.stream.seek(0)        
            return hash
        except Exception as e:
            logger.warning(f"Error when generating hash: {e}")
            return None

    def GetFileExt(self, mimetype : str):
        file_ext = mimetype.split('/')[1]
        return  f"{file_ext}"


    def GetFileUrl(self, hash : str, mimetype: str):
        file_path = self.upload_dir / self.GetFileName(hash, mimetype)
        return str(file_path)

    def GetFileName(self , hash, mimetype):
        return str(f"{hash}.{self.GetFileExt(mimetype)}")


    def FileExists(self, hash: str, mimetype: str):
        file_path = self.upload_dir / self.GetFileName(hash, mimetype)
        return os.path.exists(file_path)

    def FileRemove(self, hash, mimetype):
        try:
            file_path = self.upload_dir / self.GetFileName(hash, mimetype)
            os.remove(file_path)
            logger.info(f"File deleted successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to delete: {e}")
            return False

    def FileSave(self, file : FileStorage, filename : str):
        try:            

            file_hash = self.GetHash(file)
            mimetype = file.mimetype
            file_path = self.upload_dir / self.GetFileName(hash, mimetype)
            
            file.save(dst=file_path)
            res = {"hash": file_hash ,"file_name": filename, "type": mimetype}
            return res

        except Exception as e:
            logger.error(f"Failed to save file \"{filename}\". Error: {e}")
            return None