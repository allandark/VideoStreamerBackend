
from flask_restx import Api
from api.auth import create_api_auth, jwt
from api.video import create_api_video

def create_api(app_context):


    api = Api(
        title= "Video Streamer API",
        version= "1.0",
        description= "Video Streamer API",
        doc= "/docs"
    ) 

    api.add_namespace(create_api_auth(app_context), path="/api/auth")
    api.add_namespace(create_api_video(app_context), path="/api/video")


    return api