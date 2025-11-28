
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
        doc= "/api/doc",
        prefix="/api"
    ) 

    api.add_namespace(create_api_auth(app_context), path="/auth")
    api.add_namespace(create_api_media(app_context), path="/media")
    api.add_namespace(create_api_video_meta(app_context), path="/video_meta")
    api.add_namespace(create_api_director(app_context), path="/director")
    api.add_namespace(create_api_star(app_context), path="/star")
    api.add_namespace(create_api_genre(app_context), path="/genre")
    api.add_namespace(create_api_series(app_context), path="/series")
    api.add_namespace(create_api_user(app_context), path="/user")

    return api
    