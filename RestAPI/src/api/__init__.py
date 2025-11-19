
from flask_restx import Api
from api.auth import create_api_auth, jwt

def create_api(db_context):


    api = Api(
        title= "Video Streamer API",
        version= "1.0",
        description= "Video Streamer API",
        doc= "/docs"
    ) 

    api.add_namespace(create_api_auth(db_context), path="/api/auth")


    return api