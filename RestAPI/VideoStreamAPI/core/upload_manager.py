import hashlib
from pathlib import Path
import os
import logging
logger : logging.Logger = logging.getLogger("app")


class UploadManager:

    def __init__(self, upload_dir : Path):
        self.upload_dir = upload_dir

        self.stored_files = {}



    def AllowedMimetype(self, mimetype):
        allowed_types = ['png', 'mp4', 'svg']
        return mimetype in allowed_types

    def GetDir(self):
        return self.upload_dir

    def GetHash(self, data):
        try:
            h = hashlib.new('sha256')
            h.update(data)
            hash = h.hexdigest()            
            return hash
        except Exception as e:
            logger.warning(f"Error when generating hash: {e}")
            return None

    # def GetAllFileUrls(self):
    #     pass

    def GetFileUrl(self, hash, mimetype):
        file_ext = mimetype.split('/')[1]
        file_path = self.upload_dir / f"{hash}.{file_ext}"
        return str(file_path)

    def GetFileName(self , hash, mimetype):
        file_ext = mimetype.split('/')[1]
        return str(f"{hash}.{file_ext}")


    def FileExists(self, hash, mimetype):
        file_ext = mimetype.split('/')[1]
        file_path = self.upload_dir / f"{hash}.{file_ext}"
        return os.path.exists(file_path)

    def FileRemove(self, hash, mimetype):
        try:
            file_ext = mimetype.split('/')[1]
            file_path = self.upload_dir / f"{hash}.{file_ext}"
            os.remove(file_path)
            logger.info(f"File deleted successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to delete: {e}")
            return False

    def FileSave(self, file, filename):
        try:            
            # TODO: get file hash in chunks
            file_hash = self.GetHash(file.read())
            mimetype = (file.mimetype)
            file_ext = mimetype.split('/')[1]
            file_path = self.upload_dir / f"{file_hash}.{file_ext}"
            file.stream.seek(0)
            file.save(dst=file_path)
            res = {"hash": file_hash ,"file_name": filename, "type": mimetype}
            return res

        except Exception as e:
            logger.error(f"Failed to save file \"{filename}\". Error: {e}")
            return None