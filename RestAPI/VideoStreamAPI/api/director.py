from flask_restx import Namespace, Resource, fields, Model
from flask_jwt_extended import JWTManager
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import logging
logger : logging.Logger = logging.getLogger("app")

from VideoStreamAPI.api.api_models import get_director_model, get_director_request_model



jwt = JWTManager()

authorizations = {
    "jsonWebToken":{
        "type": "apiKey",
        "in": "header",
        "name": "Authorization"
    }
}

def create_api_director(app_context):
    api: Namespace = Namespace("director", description="Director", authorizations=authorizations)

    director_model = get_director_model(api)
    director_request_model = get_director_request_model(api)


    @api.route('')
    class Director(Resource):

        @api.doc('Get all directors')
        # @api.expect(request_parser)
        @api.marshal_list_with(director_model)
        # TODO: add filtering
        def get(self):
            # args = request_parser.parse_args()
            directors = app_context.db_context.directors.GetAll()
            return directors

        @api.doc('Create new director')
        @api.expect(director_request_model)
        @api.marshal_with(director_model, code=201)
        def post(self):            
            director = app_context.db_context.directors.Create(request.json)
            return director, 200


    @api.route('/<int:id>')
    class DirectorID(Resource):
        @api.doc('Get director by id')
        @api.marshal_with(director_model)
        def get(self, id):
            director = app_context.db_context.directors.Get(id)
            if director is None:
                return director, 404
            return director, 200


        @api.doc('Update director with id')
        @api.expect(director_model)
        @api.marshal_with(director_model)
        def put(self, id):
            director = app_context.db_context.directors.Get(id)
            if director is None:
                return director, 404
            director = app_context.db_context.directors.Update(request.json)
            return director, 200

        @api.doc('Delete director with id')
        def delete(self, id):
            director = app_context.db_context.directors.Get(id)
            if director is None:
                return {"error": "director not found"}, 404
            res = app_context.db_context.directors.Delete(id)
            if not res:
                return {"error", "bad request"}, 400
            return {"message": "director was deleted"}, 200

    return api

