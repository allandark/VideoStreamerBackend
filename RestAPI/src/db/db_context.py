
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.engine import URL
from .models import Base, UserModel, VideoMetaDataModel, SubtitlesModel
from .models import GenreModel, StarModel, SeriesModel, DirectorModel
from .services.crud import CrudService
import os

import datetime

import logging
logger : logging.Logger = logging.getLogger("app")


def load_pw_file():
    file_path = os.getenv("MYSQL_ROOT_PASSWORD_FILE") 
    logger.debug(f"Reading file: {file_path}")
    with open(file_path) as f:
        data = f.read()
        return data
    return None

class DatabaseContext:
    def __init__(self, create_tables: bool = False, seed: bool = False ):
        logger.info("Initializing database")

        self.db_password = load_pw_file()
        self.db_host = os.getenv("MYSQL_HOST")        
        self.db_port = os.getenv("MYSQL_PORT")        
        self.db_name = os.getenv("MYSQL_DATABASE")
        logger.debug(f"DB connection info: host={self.db_host}, port={self.db_port}, name={self.db_name}")
        connection_url = URL.create(
            "mysql+mysqlconnector",
            username="root",
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name
        )

        self.engine = create_engine(connection_url, echo=False, future=True)
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
        self.subtitles = CrudService(self.db_session, SubtitlesModel)

        if create_tables:
            self.CreateTables()
        if seed:
            self.Seed()


    def CreateTables(self):
        try:
            self.metadata_obj.create_all(self.engine)
            logger.debug("Tables created")
        except Exception as e:
            logger.error(f"CreateTables failed: {e}")

    def Seed(self):
        with self.db_session() as session:        
            try:

                user = UserModel()
                user.email = "john@doe.dk"
                user.hashed_password = "1234"
                user.creation_date = datetime.datetime.now().isoformat()
                user.user_type = "admin"      
                user.user_name = "john"          
                session.add(user)

                genre = GenreModel() 
                genre.name = "Action"
                genre.rating = 4.5
                
                session.add(genre)

                actor = StarModel()
                actor.full_name = "Cicholas Nage"
                actor.rating = 2.5


                video = VideoMetaDataModel()
                video.file_path = "/some/path"
                video.duration_seconds = 500
                video.language = "English"
                video.screen_height = 0
                video.screen_width = 0
                video.rating = 0.5
                video.upload_date = datetime.datetime.now().isoformat()
                video.title = "Some movie title"
                session.add(video)

                genre.videos.append(video)

                session.commit()
                logger.debug(f"User added to db: {user}")
            except Exception as e:
                session.rollback()
                logger.error(f"Failed top add models: {e}")

