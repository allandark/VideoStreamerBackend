from flask_restx import Namespace, Resource, fields, Model
from flask_jwt_extended import JWTManager
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from VideoStreamAPI.db.models import SubtitlesModel
from .api_models import get_star_model, get_star_request_model

from datetime import datetime, date
import logging
logger : logging.Logger = logging.getLogger("app")

jwt = JWTManager()

authorizations = {
    "jsonWebToken":{
        "type": "apiKey",
        "in": "header",
        "name": "Authorization"
    }
}

def create_api_star(app_context):
    api: Namespace = Namespace("star", description="Stars/actor/actresses namespace", authorizations=authorizations)

    star_model = get_star_model(api)
    star_request_model = get_star_request_model(api)


    @api.route('/')
    class Star(Resource):

        @api.doc('Get all stars')
        # @api.expect(request_parser)
        @api.marshal_list_with(star_model)
        # TODO: add filtering
        def get(self):
            # args = request_parser.parse_args()
            stars = app_context.db_context.stars.GetAll()
            return stars

        @api.doc('Create new star')
        @api.expect(star_request_model)
        @api.marshal_with(star_model, code=201)
        def post(self):            
            star = app_context.db_context.stars.Create(request.json)
            return star, 200


    @api.route('/<int:id>')
    class StarID(Resource):
        @api.doc('Get star by id')
        @api.marshal_with(star_model)
        def get(self, id):
            star = app_context.db_context.stars.Get(id)
            if star is None:
                return star, 404
            return star, 200


        @api.doc('Update star with id')
        @api.expect(star_model)
        @api.marshal_with(star_model)
        def put(self, id):
            star = app_context.db_context.stars.Get(id)
            if star is None:
                return star, 404
            star = app_context.db_context.stars.Update(request.json)
            return star, 200

        @api.doc('Delete star with id')
        def delete(self, id):
            star = app_context.db_context.stars.Get(id)
            if star is None:
                return {"error": "star not found"}, 404
            res = app_context.db_context.stars.Delete(id)
            if not res:
                return {"error", "bad request"}, 400
            return {"message": "star was deleted"}, 200

    return api

