from flask_restx import Namespace, Resource, fields, Model
from flask_jwt_extended import JWTManager
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from datetime import datetime, date
import logging
logger : logging.Logger = logging.getLogger("app")

from VideoStreamAPI.api.api_models import get_genre_model, get_genre_request_model



jwt = JWTManager()

authorizations = {
    "jsonWebToken":{
        "type": "apiKey",
        "in": "header",
        "name": "Authorization"
    }
}

def create_api_genre(app_context):
    api: Namespace = Namespace("genre", description="Video Genre namespace", authorizations=authorizations)

    genre_model = get_genre_model(api)
    genre_request_model = get_genre_request_model(api)


    @api.route('/')
    class Genre(Resource):

        @api.doc('Get all genres')
        # @api.expect(request_parser)
        @api.marshal_list_with(genre_model)
        # TODO: add filtering
        def get(self):
            # args = request_parser.parse_args()
            genres = app_context.db_context.genres.GetAll()
            return genres

        @api.doc('Create new genre')
        @api.expect(genre_request_model)
        @api.marshal_with(genre_model, code=201)
        def post(self):
            
            genre = app_context.db_context.genres.Create(request.json)

            return genre, 200


    @api.route('/<int:id>')
    class GenreID(Resource):
        @api.doc('Get genre by id')
        @api.marshal_with(genre_model)
        def get(self, id):
            genre = app_context.db_context.genres.Get(id)
            if genre is None:
                return genre, 404
            return genre, 200


        @api.doc('Update genre with id')
        @api.expect(genre_model)
        @api.marshal_with(genre_model)
        def put(self, id):
            genre = app_context.db_context.genres.Get(id)
            if genre is None:
                return genre, 404
            genre = app_context.db_context.genres.Update(request.json)
            return genre, 200

        @api.doc('Delete genre with id')
        def delete(self, id):
            genre = app_context.db_context.genres.Get(id)
            if genre is None:
                return {"error": "genre not found"}, 404
            res = app_context.db_context.genres.Delete(id)
            if not res:
                return {"error", "bad request"}, 400
            return {"message": "genre was deleted"}, 200

    return api

