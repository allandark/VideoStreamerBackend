from VideoStreamAPI.api.api_models import get_series_model, get_series_request_model
from flask_restx import Namespace, Resource, fields, Model
from flask_jwt_extended import JWTManager
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import logging
logger: logging.Logger = logging.getLogger("app")


jwt = JWTManager()

authorizations = {
    "jsonWebToken": {
        "type": "apiKey",
        "in": "header",
        "name": "Authorization"
    }
}


def create_api_series(app_context):
    api: Namespace = Namespace(
        "series", description="Video series", authorizations=authorizations)

    series_model = get_series_model(api)
    series_request_model = get_series_request_model(api)

    @api.route('')
    class Series(Resource):

        @api.doc('Get all series')
        # @api.expect(request_parser)
        @api.marshal_list_with(series_model)
        # TODO: add filtering
        def get(self):
            # args = request_parser.parse_args()
            series = app_context.db_context.series.GetAll()
            return series

        @api.doc('Create new series')
        @api.expect(series_request_model)
        @api.marshal_with(series_model, code=201)
        def post(self):
            series = app_context.db_context.series.Create(request.json)
            return series, 200

    @api.route('/<int:id>')
    class SeriesID(Resource):
        @api.doc('Get series by id')
        @api.marshal_with(series_model)
        def get(self, id):
            series = app_context.db_context.series.Get(id)
            if series is None:
                return series, 404
            return series, 200

        @api.doc('Update series with id')
        @api.expect(series_model)
        @api.marshal_with(series_model)
        def put(self, id):
            genre = app_context.db_context.series.Get(id)
            if genre is None:
                return genre, 404
            genre = app_context.db_context.series.Update(request.json)
            return genre, 200

        @api.doc('Delete series with id')
        def delete(self, id):
            series = app_context.db_context.series.Get(id)
            if series is None:
                return {"error": "series not found"}, 404
            res = app_context.db_context.series.Delete(id)
            if not res:
                return {"error", "bad request"}, 400
            return {"message": "series was deleted"}, 200

    return api
