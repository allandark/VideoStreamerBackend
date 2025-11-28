from flask_restx import Namespace, Resource, fields, Model
from flask_jwt_extended import JWTManager
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import logging
logger : logging.Logger = logging.getLogger("app")

from VideoStreamAPI.api.api_models import get_user_model, get_user_request_model



jwt = JWTManager()

authorizations = {
    "jsonWebToken":{
        "type": "apiKey",
        "in": "header",
        "name": "Authorization"
    }
}

def create_api_user(app_context):
    api: Namespace = Namespace("user", description="User", authorizations=authorizations)

    user_model = get_user_model(api)
    user_request_model = get_user_request_model(api)


    @api.route('/')
    class User(Resource):

        @api.doc('Get all users')
        # @api.expect(request_parser)
        @api.marshal_list_with(user_model)
        # TODO: add filtering
        def get(self):
            # args = request_parser.parse_args()
            users = app_context.db_context.users.GetAll()
            

            return users

        @api.doc('Create new user')
        @api.expect(user_request_model)
        @api.marshal_with(user_model, code=201)
        def post(self):
            
            user = app_context.db_context.users.Create(request.json)
            return user, 200


    @api.route('/<int:id>')
    class UserID(Resource):
        @api.doc('Get user by id')
        @api.marshal_with(user_model)
        def get(self, id):
            user = app_context.db_context.users.Get(id)
            if user is None:
                return user, 404
            return user, 200


        @api.doc('Update user with id')
        @api.expect(user_model)
        @api.marshal_with(user_model)
        def put(self, id):
            user = app_context.db_context.users.Get(id)
            if user is None:
                return user, 404
            user = app_context.db_context.users.Update(request.json)
            return user, 200

        @api.doc('Delete user with id')
        def delete(self, id):
            user = app_context.db_context.users.Get(id)
            if user is None:
                return {"error": "user not found"}, 404
            res = app_context.db_context.users.Delete(id)
            if not res:
                return {"error", "bad request"}, 400
            return {"message": "user was deleted"}, 200

    return api

