from flask_restx import Namespace, Resource, fields, Model
from flask_jwt_extended import JWTManager
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import logging
logger : logging.Logger = logging.getLogger("app")

from VideoStreamAPI.api.api_models import get_subtitle_model, get_video_meta_data_request_model, get_video_meta_response_model
from VideoStreamAPI.api.api_models import get_director_model, get_genre_model, get_star_model, get_series_model, get_video_request_parser

jwt = JWTManager()

authorizations = {
    "jsonWebToken":{
        "type": "apiKey",
        "in": "header",
        "name": "Authorization"
    }
}

def create_api_video_meta(app_context):
    api: Namespace = Namespace("video_meta", description="Video Meta data namespace for database tracking of videos", authorizations=authorizations)

    # Models
    subtitle_model = get_subtitle_model(api)
    star_model = get_star_model(api=api, include_relationship=False)
    director_model = get_director_model(api=api, include_relationship=False)
    genre_model = get_genre_model(api=api, include_relationship=False)
    series_model = get_series_model(api=api, include_relationship=False)
    video_meta_response_model = get_video_meta_response_model(api)
    video_meta_data_request_model = get_video_meta_data_request_model(api)

    # Parsers
    request_parser = get_video_request_parser(api)

    @api.route('/')
    class VideoMeta(Resource):

        @api.doc('Get all video meta data with filtering queries')
        @api.expect(request_parser)
        @api.marshal_list_with(video_meta_response_model)
        # TODO: add filtering
        def get(self):
            args = request_parser.parse_args()
            videos = app_context.db_context.videos.GetAll(args)
       
            return videos

        @api.doc('Create new video meta data')
        @api.expect(video_meta_data_request_model)
        @api.marshal_with(video_meta_response_model, code=201)
        def post(self):

            media_id = request.json['media_id']
            media = app_context.db_context.media.Get(media_id)
            if media is None:
                return media, 400

            if not app_context.media_manager.uploader.FileExists(media['hash'], media['mimetype']):
                return media, 400
            
            file_name =  app_context.media_manager.uploader.GetFileName(media['hash'], media['mimetype'])
            meta_data = app_context.media_manager.video_manager.LoadData(file_name)

            if app_context.media_manager.video_manager.DirExists(media['hash']):
                app_context.media_manager.video_manager.DirRemove(media['hash'])

            hls_data = app_context.media_manager.video_manager.CreateHls(
                meta_data, media['hash'], 
                hls_playlist_base_url=f"http://localhost:5000/api/media/playlist/{media_id}/",
                hls_segment_base_url=f"http://localhost:5000/api/media/chunk/{media_id}/")
            if not hls_data['build_status']:
                return None, 400

            file_name_no_ext = str(file_name).split('.')[0]
            upload_date = datetime.now().isoformat()
            data = {
                'title': request.json['title'],
                'media_id': media_id,
                'description': request.json['description'],
                'file_path': file_name_no_ext,
                'upload_date' : upload_date,            
                'duration_seconds': meta_data.format['duration'],
                'screen_width' : meta_data.video_tracks[0]['width'],
                'screen_height' : meta_data.video_tracks[0]['height'],
                'rating': request.json['rating'],
                'language': request.json['language'],
                'stars': request.json['stars'],
                'genres': request.json['genres'],
                'directors': request.json['directors'],
                'series': request.json['series'],
                'subtitles': request.json['subtitles'],
            }
            video = app_context.db_context.videos.Create(data)

            return video, 200


    @api.route('/<int:id>')
    class VideoMetaID(Resource):
        @api.doc('Get video meta data by id')
        @api.marshal_with(video_meta_response_model)
        def get(self, id):
            video = app_context.db_context.videos.Get(id)
            if video is None:
                return video, 404

            return video, 200


        @api.doc('Update video meta data with id')
        @api.expect(video_meta_response_model)
        @api.marshal_with(video_meta_response_model)
        def put(self, id):
            video = app_context.db_context.videos.Get(id)
            if video is None:
                return video, 404
            video = app_context.db_context.videos.Update(request.json)

            return video, 200

        @api.doc('Delete video meta data with id')
        def delete(self, id):
            video = app_context.db_context.videos.Get(id)
            if video is None:
                return {"error": "video not found"}, 404
            res = app_context.db_context.videos.Delete(id)
            media = app_context.db_context.media.Get(video['media_id'])
            app_context.media_manager.video_manager.DirRemove(media['hash'])
            if not res:
                return {"error", "bad request"}, 400
            return {"message": "video meta data deleted"}, 200

    return api

