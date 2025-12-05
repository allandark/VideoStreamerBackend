
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.engine import URL
import os
import datetime
import logging
logger : logging.Logger = logging.getLogger("app")

from VideoStreamAPI.db.models import Base, UserModel, VideoMetaDataModel, MediaTaskModel
from VideoStreamAPI.db.models import GenreModel, StarModel, SeriesModel, DirectorModel, MediaMetaDataModel
from VideoStreamAPI.db.services.crud import CrudService


def load_pw_file():
    file_path = os.getenv("MYSQL_ROOT_PASSWORD_FILE") 
    logger.debug(f"Reading file: {file_path}")
    with open(file_path) as f:
        data = f.read()
        return data
    return None

class DatabaseContext:
    def __init__(self, create_tables: bool = False ):
        logger.info("Initializing database")

        self.db_password = load_pw_file()
        self.db_host = os.getenv("MYSQL_HOST")        
        self.db_port = os.getenv("MYSQL_PORT")        
        self.db_name = os.getenv("MYSQL_DATABASE")
        logger.debug(f"DB connection info: host={self.db_host}, port={self.db_port}, name={self.db_name}")
        self.connection_url = URL.create(
            "mysql+mysqlconnector",
            username="root",
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name
        )

        self.engine = create_engine(self.connection_url, echo=False, future=True)
        self.db_session = sessionmaker(
                            bind=self.engine, 
                            expire_on_commit=False,
                            autoflush=False,
                            future=True)


        self.metadata_obj = Base.metadata

        # CRUD services
        self.users = CrudService(self.db_session, UserModel)
        self.videos = CrudService(self.db_session, VideoMetaDataModel)
        self.stars = CrudService(self.db_session, StarModel)
        self.directors = CrudService(self.db_session, DirectorModel)
        self.series = CrudService(self.db_session, SeriesModel)
        self.genres = CrudService(self.db_session, GenreModel)        
        self.media = CrudService(self.db_session, MediaMetaDataModel)
        self.tasks = CrudService(self.db_session, MediaTaskModel)

        if create_tables:
            self.CreateTables()

    def CreateTables(self):
        try:
            self.metadata_obj.create_all(self.engine, checkfirst=True)
            logger.debug("Tables created")
        except Exception as e:
            logger.error(f"CreateTables failed: {e}")

   