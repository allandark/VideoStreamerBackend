from flask_restx import Namespace, Resource, fields, Model
from flask_jwt_extended import JWTManager
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from .api_models import get_user_request_model

jwt = JWTManager()

authorizations = {
    "jsonWebToken":{
        "type": "apiKey",
        "in": "header",
        "name": "Authorization"
    }
}

def create_api_auth(app_context):

    api: Namespace = Namespace("auth", description="Authentication namespace", authorizations=authorizations)


    user_request_model = get_user_request_model(api)

    @api.route('/login')
    class Auth(Resource):
        @api.doc('Login to user')
        @api.expect(user_request_model)
        def post(self):
            # TODO
            user = app_context.db_context.users.GetAttr("user_name", request.json['name'])

            return {"messeage", "status"}, 200


    return api