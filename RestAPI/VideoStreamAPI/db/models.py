from sqlalchemy import ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.types import String,  DateTime, JSON, Boolean
from sqlalchemy import JSON
from typing import List, Dict, Any, Optional
import logging
logger: logging.Logger = logging.getLogger("app")


class Base(DeclarativeBase):
    pass


# Association/join tables
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

video_tag_table = Table(
    "VIDEO_TAGS",
    Base.metadata,
    Column("media_id", ForeignKey("VIDEO_META_DATA.id"), primary_key=True),
    Column("tag_id", ForeignKey("TAG.id"), primary_key=True),
)


class VideoMetaDataModel(Base):
    __tablename__ = "VIDEO_META_DATA"
    # Columns
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[String] = mapped_column(String(256))
    description: Mapped[String] = mapped_column(String(1024))
    duration_seconds: Mapped[int]
    views: Mapped[int]
    rating: Mapped[float]
    upload_date: Mapped[DateTime] = mapped_column(DateTime())

    media_id: Mapped[int] = mapped_column(
        ForeignKey("MEDIA_META_DATA.id"), unique=True)
    # Relationships

    media: Mapped["MediaMetaDataModel"] = relationship(back_populates="video")
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

    tags: Mapped[List["TagModel"]] = relationship(
        secondary=video_tag_table,
        back_populates="videos")

    def __repr__(self) -> str:
        return "".join((f"VideoMetaDataModel(id={self.id!r}, title={self.title!r}, ",
                        f"file_path={self.file_path!r}, language={self.language!r}, duration_seconds={self.duration_seconds!r}, ",
                        f", screen_width={self.screen_width!r}, screen_height={self.screen_height!r}",
                        f", rating={self.rating!r}, upload_date={self.upload_date!r}",
                        f")"))


class DirectorModel(Base):
    __tablename__ = "DIRECTOR"
    # Columns
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
    # Columns
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
    # Columns
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
    # Columns
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


class UserModel(Base):
    __tablename__ = "USER"
    # Columns
    id: Mapped[int] = mapped_column(primary_key=True)
    user_name: Mapped[String] = mapped_column(String(256))
    hashed_password: Mapped[String] = mapped_column(String(256))
    email: Mapped[String] = mapped_column(String(256))
    user_type: Mapped[String] = mapped_column(String(256))
    creation_date: Mapped[DateTime] = mapped_column(DateTime())

    def __repr__(self) -> str:
        return "".join((f"UserModel(id={self.id!r}, user_name={self.user_name!r}, ",
                        f", email={self.email!r}, user_type={self.user_type!r}, creation_date={self.creation_date!r}",
                        f")"))


class TagModel(Base):
    __tablename__ = "TAG"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[String] = mapped_column(String(256))

    videos: Mapped[List["VideoMetaDataModel"]] = relationship(
        secondary=video_tag_table,
        back_populates="tags"
    )


class MediaMetaDataModel(Base):
    __tablename__ = "MEDIA_META_DATA"

    id: Mapped[int] = mapped_column(primary_key=True)
    hash: Mapped[String] = mapped_column(String(64))
    name: Mapped[String] = mapped_column(String(256))
    mimetype: Mapped[String] = mapped_column(String(64))
    master_file: Mapped[Boolean] = mapped_column(
        Boolean, nullable=False, default=False)
    video_tracks: Mapped[JSON] = mapped_column(
        JSON, nullable=False, default=dict)
    audio_tracks: Mapped[JSON] = mapped_column(
        JSON, nullable=False, default=dict)
    subtitle_tracks: Mapped[JSON] = mapped_column(
        JSON, nullable=False, default=dict)
    thumbnail: Mapped[Boolean] = mapped_column(Boolean, default=False)

    # Relationships

    tasks: Mapped[List["MediaTaskModel"]] = relationship(
        "MediaTaskModel", back_populates="media", cascade="all, delete-orphan"
    )
    video: Mapped["VideoMetaDataModel"] = relationship(
        back_populates="media",
        uselist=False
    )

    def __repr__(self) -> str:
        return "".join((f"MediaMetaDataModel(id={self.id!r}, hash={self.hash!r}, ",
                        f", name={self.name!r}, mimetype={self.mimetype!r}",
                        f")"))


class MediaTaskModel(Base):
    __tablename__ = "MEDIA_TASK"
    id: Mapped[int] = mapped_column(primary_key=True)
    task_type: Mapped[String] = mapped_column(String(64))
    status: Mapped[String] = mapped_column(String(64))
    error_message: Mapped[String] = mapped_column(String(512))
    creation_date: Mapped[DateTime] = mapped_column(DateTime())
    params: Mapped[Dict[str, Any]] = mapped_column(
        MutableDict.as_mutable(JSON),
        nullable=False,
        default=dict
    )

    media_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("MEDIA_META_DATA.id", ondelete="SET NULL"),
        nullable=True,
        default=None
    )
    media: Mapped["MediaMetaDataModel"] = relationship(
        "MediaMetaDataModel", back_populates="tasks", passive_deletes=True)

    def __repr__(self) -> str:
        return "".join((f"MediaTaskModel(id={self.id!r}, task_type={self.task_type!r}, ",
                        f", status={self.status!r}, creation_date={self.creation_date!r}",
                        f"creation_date={self.error_message!r}, media_id={self.media_id!r})"))
