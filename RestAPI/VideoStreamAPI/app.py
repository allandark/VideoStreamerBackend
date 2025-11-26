from flask import Flask
from flask_cors import CORS

from api import create_api, jwt
from core.custom_formatter import CustomFormatter, InitLogger
from core.media_manager import MediaManager
from db.db_context import DatabaseContext
from dataclasses import dataclass
import os

import logging
logger : logging.Logger = logging.getLogger("app")



from core.upload_manager import UploadManager

@dataclass
class AppContext:
    """ Context class meant to dependencies to 

    """
    media_manager : MediaManager
    db_context : DatabaseContext
    

def create_app():
    
    app = Flask(__name__)
    CORS(app, supports_credentials=True, origins=["http://localhost:5173", "http://localhost:8081"])
    InitLogger(app)
    logger.info("Initializing server ...")


    db_context = DatabaseContext(create_tables=True, seed=False)
    
    # TEMP
    abs_path = f"{os.getcwd()}/testfiles"
    media_manager = MediaManager(abs_video_dir=abs_path)

    # END TEMP


    app_context = AppContext(
        db_context = db_context,
        media_manager = media_manager
    )

    api = create_api(app_context)
    api.init_app(app,docs=True)
    jwt.init_app(app)


    return app

if __name__ == "__main__":
    app = create_app()
    logger.info("Starting server ...")
    app.run(host='0.0.0.0', port=5000)