from flask import Flask
from flask_cors import CORS
from dataclasses import dataclass
import os
import logging
logger : logging.Logger = logging.getLogger("app")

from VideoStreamAPI.api import create_api, jwt
from VideoStreamAPI.core.custom_formatter import InitLogger
from VideoStreamAPI.core.media_manager import MediaManager
from VideoStreamAPI.db.db_context import DatabaseContext


@dataclass
class AppContext:
    """ Context class for passing db_context and media_context to api endpoints
    """
    media_manager : MediaManager
    db_context : DatabaseContext
    

def create_app():
    """ Create flask server
    """
    
    app = Flask(__name__)
    CORS(app, supports_credentials=True, origins=["http://localhost:8080","http://localhost:5173"])
    InitLogger(app)
    logger.info("Initializing server ...")


    db_context = DatabaseContext(create_tables=True)    
    media_manager = MediaManager(abs_video_dir="/var/media", db=db_context)

    app_context = AppContext(
        db_context = db_context,
        media_manager = media_manager
    )

    api = create_api(app_context)
    api.init_app(app,docs=True)
    jwt.init_app(app)


    return app


app = create_app()

if __name__ == "__main__":
    app.run()
  