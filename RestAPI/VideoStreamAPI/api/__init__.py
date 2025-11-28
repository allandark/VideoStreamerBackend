
from flask_restx import Api
from VideoStreamAPI.api.auth import create_api_auth, jwt
from VideoStreamAPI.api.media import create_api_media
from VideoStreamAPI.api.director import create_api_director
from VideoStreamAPI.api.star import create_api_star
from VideoStreamAPI.api.genre import create_api_genre
from VideoStreamAPI.api.series import create_api_series
from VideoStreamAPI.api.video_meta_data import create_api_video_meta
from VideoStreamAPI.api.user import create_api_user

def create_api(app_context):

    api = Api(
        title= "Video Streamer API",
        version= "1.0",
        description= "Video Streamer API",
        doc= "/docs"
    ) 

    api.add_namespace(create_api_auth(app_context), path="/api/auth")
    api.add_namespace(create_api_media(app_context), path="/api/media")
    api.add_namespace(create_api_video_meta(app_context), path="/api/video_meta")
    api.add_namespace(create_api_director(app_context), path="/api/director")
    api.add_namespace(create_api_star(app_context), path="/api/star")
    api.add_namespace(create_api_genre(app_context), path="/api/genre")
    api.add_namespace(create_api_series(app_context), path="/api/series")
    api.add_namespace(create_api_user(app_context), path="/api/user")

    return api
    