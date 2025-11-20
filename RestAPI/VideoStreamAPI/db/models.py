from sqlalchemy import ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase
from sqlalchemy.types import String, Date
from typing import List

import logging
logger : logging.Logger = logging.getLogger("app")

class Base(DeclarativeBase):
  pass

# Assosiation tables
video_star_table = Table(
    "VIDEO_STAR",
    Base.metadata,
    Column("media_id", ForeignKey("VIDEO_META_DATA.id"), primary_key=True),
    Column("star_id", ForeignKey("STAR.id"), primary_key=True),
)

video_director_table = Table(
    "VIDEO_DIRECTOR",
    Base.metadata,
    Column("media_id", ForeignKey("VIDEO_META_DATA.id"), primary_key=True),
    Column("director_id", ForeignKey("DIRECTOR.id"), primary_key=True),
)

video_genre_table = Table(
    "VIDEO_GENRE",
    Base.metadata,
    Column("media_id", ForeignKey("VIDEO_META_DATA.id"), primary_key=True),
    Column("genre_id", ForeignKey("GENRE.id"), primary_key=True),
)

video_series_table = Table(
    "VIDEO_SERIES",
    Base.metadata,
    Column("media_id", ForeignKey("VIDEO_META_DATA.id"), primary_key=True),
    Column("series_id", ForeignKey("SERIES.id"), primary_key=True),
)


class VideoMetaDataModel(Base):
  __tablename__ = "VIDEO_META_DATA"
  #Columns
  id: Mapped[int] = mapped_column(primary_key=True)
  title: Mapped[String] = mapped_column(String(256))
  file_path: Mapped[String] = mapped_column(String(256))
  language: Mapped[String] = mapped_column(String(256))
  duration_seconds: Mapped[int] 
  screen_width: Mapped[int] 
  screen_height: Mapped[int] 
  rating: Mapped[float] 
  upload_date: Mapped[Date] = mapped_column(Date())
  
  # Relationships
  subtitles: Mapped[List["SubtitlesModel"]] = relationship(back_populates="video")
  stars: Mapped[List["StarModel"]] = relationship(
      secondary=video_star_table, 
      back_populates="videos")

  directors: Mapped[List["DirectorModel"]] = relationship(
      secondary=video_director_table, 
      back_populates="videos")

  genres: Mapped[List["GenreModel"]] = relationship(
      secondary=video_genre_table, 
      back_populates="videos")

  series: Mapped[List["SeriesModel"]] = relationship(
      secondary=video_series_table, 
      back_populates="videos")
    
  def __repr__(self) -> str:
    return "".join((f"VideoMetaDataModel(id={self.id!r}, title={self.title!r}, ",
            f"file_path={self.file_path!r}, language={self.language!r}, duration_seconds={self.duration_seconds!r}, ",
            f", screen_width={self.screen_width!r}, screen_height={self.screen_height!r}",  
            f", rating={self.rating!r}, upload_date={self.upload_date!r}",
            f")"))


class DirectorModel(Base):
  __tablename__ = "DIRECTOR"
  #Columns
  id: Mapped[int] = mapped_column(primary_key=True)
  full_name: Mapped[String] = mapped_column(String(256))
  rating: Mapped[float]

  videos: Mapped[List["VideoMetaDataModel"]] = relationship(
    secondary=video_director_table, 
    back_populates="directors"
  )


  def __repr__(self) -> str:
    return "".join((f"DirectorModel(id={self.id!r}, full_name={self.full_name!r}, ",
            f", rating={self.rating!r}",
            f")"))


class StarModel(Base):
  __tablename__ = "STAR"
  #Columns
  id: Mapped[int] = mapped_column(primary_key=True)
  full_name: Mapped[String] = mapped_column(String(256))
  rating: Mapped[float]
  
  videos: Mapped[List["VideoMetaDataModel"]] = relationship(
    secondary=video_star_table, 
    back_populates="stars"
  )

  
  def __repr__(self) -> str:
    return "".join((f"StarModel(id={self.id!r}, full_name={self.full_name!r}, ",
            f", rating={self.rating!r}",
            f")"))


class GenreModel(Base):
  __tablename__ = "GENRE"
  #Columns
  id: Mapped[int] = mapped_column(primary_key=True)
  name: Mapped[String] = mapped_column(String(256))
  rating: Mapped[float]

  videos: Mapped[List["VideoMetaDataModel"]] = relationship(
    secondary=video_genre_table, 
    back_populates="genres"
  )


  def __repr__(self) -> str:
    return "".join((f"GenreModel(id={self.id!r}, name={self.name!r}, ",
            f", rating={self.rating!r}",
            f")"))


class SeriesModel(Base):
  __tablename__ = "SERIES"
  #Columns
  id: Mapped[int] = mapped_column(primary_key=True)
  name: Mapped[String] = mapped_column(String(256))
  rating: Mapped[float]

  videos: Mapped[List["VideoMetaDataModel"]] = relationship(
    secondary=video_series_table, 
    back_populates="series"
  )


  def __repr__(self) -> str:
    return "".join((f"SeriesModel(id={self.id!r}, name={self.name!r}, ",
            f", rating={self.rating!r}",
            f")"))


class SubtitlesModel(Base):
  __tablename__ = "SUBTITLES"
  #Columns
  id: Mapped[int] = mapped_column(primary_key=True)
  name: Mapped[String] = mapped_column(String(256))
  file_path: Mapped[String] = mapped_column(String(256))

  
  # Foreign key to VideoMetaDataModel
  video_id: Mapped[int] = mapped_column(ForeignKey("VIDEO_META_DATA.id"))

  # Relationship back to parent
  video: Mapped["VideoMetaDataModel"] = relationship(back_populates="subtitles")


  def __repr__(self) -> str:
    return "".join((f"SubtitlesModel(id={self.id!r}, name={self.name!r}, ",
            f", file_path={self.file_path!r}",
            f")"))


class UserModel(Base):
  __tablename__ = "USER"
  #Columns
  id: Mapped[int] = mapped_column(primary_key=True)
  user_name: Mapped[String] = mapped_column(String(256))
  hashed_password: Mapped[String] = mapped_column(String(256))
  email: Mapped[String] = mapped_column(String(256))
  user_type: Mapped[String] = mapped_column(String(256))
  creation_date: Mapped[Date] = mapped_column(Date())

  def __repr__(self) -> str:
    return "".join((f"UserModel(id={self.id!r}, user_name={self.user_name!r}, ",
            f", email={self.email!r}, user_type={self.user_type!r}, creation_date={self.creation_date!r}",
            f")"))
  
