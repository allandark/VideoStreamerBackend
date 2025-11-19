from flask import Flask
from api import create_api, jwt
from core.custom_formatter import CustomFormatter, InitLogger
from db.db_context import DatabaseContext

import logging
logger : logging.Logger = logging.getLogger("app")

def create_app():
    
    
    app = Flask(__name__)
    InitLogger(app)
    logger.info("Initializing API")
    
    db_context = DatabaseContext(create_tables=False, seed=False)


    users = db_context.users.Get(1)
    logger.debug(users)
    videos = db_context.videos.GetAll()
    logger.debug(videos)
    stars = db_context.stars.GetAll()
    logger.debug(stars)

    api = create_api(db_context)
    api.init_app(app,docs=True)
    jwt.init_app(app)


    return app

if __name__ == "__main__":
    app = create_app()
    logger.info("Starting server")
    app.run(host='0.0.0.0', port=5000)