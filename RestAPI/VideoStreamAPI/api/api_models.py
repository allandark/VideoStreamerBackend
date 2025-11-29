
from flask_restx import Namespace, Resource, fields, Model

def get_subtitle_model(api):
    return api.model('SubtitleResponseModel', {
        'id': fields.Integer(required=True)
        })

def get_star_model(api, include_relationship=True):
    if include_relationship:
        video_model = get_video_meta_response_model(api=api, include_relationship=False)
        return api.model('StarResponseModel', {
            'id': fields.Integer(required=True),
            'full_name': fields.String(required=True),
            'rating': fields.Float(required=True),
            'videos': fields.List(fields.Nested(video_model))
        })
    else:
        return api.model('StarResponseModel', {
            'id': fields.Integer(required=True)
        })


def get_star_request_model(api):
    video_model = get_video_meta_response_model(api=api,include_relationship=False)
    return api.model('StarRequestModel', {
        'full_name': fields.String(required=True),
        'rating': fields.Float(required=True),
        'videos': fields.List(fields.Nested(video_model))
    })

def get_director_model(api,  include_relationship=True):
    if include_relationship:        
        videos_model = get_video_meta_response_model(api=api, include_relationship=False)
        return api.model('DirectorResponseModel', {
            'id': fields.Integer(required=True),
            'full_name': fields.String(required=True),
            'rating': fields.Float(required=True),
            'videos': fields.List(fields.Nested(videos_model))
        })
    else:
        return api.model('DirectorResponseModel', {
            'id': fields.Integer(required=True),
            'full_name': fields.String(required=True),
            'rating': fields.Float(required=True)
        })

def get_director_request_model(api,  include_relationship=True):
    videos_model = get_video_meta_response_model(api=api, include_relationship=False)
    return api.model('DirectorResponseModel', {
        'full_name': fields.String(required=True),
        'rating': fields.Float(required=True),
        'videos': fields.List(fields.Nested(videos_model))
    })


def get_genre_model(api,  include_relationship=True):
    if include_relationship:
        videos = get_video_meta_response_model(api=api, include_relationship=False)
        return api.model('GenreResponseModel', {
            'id': fields.Integer(required=True),
            'name': fields.String(required=True),
            'rating': fields.Float(required=True),
            'videos' : fields.List(fields.Nested(videos))
        })
    else:
        return api.model('GenreResponseModel', {
            'id': fields.Integer(required=True)
        })

def get_genre_request_model(api):
    videos = get_video_meta_response_model(api=api, include_relationship=False)
    return api.model('GenreRequestModel', {
        'name': fields.String(required=True),
        'rating': fields.Float(required=True),
        'videos' : fields.List(fields.Nested(videos))
    })

def get_series_model(api, include_relationship=True):
    if include_relationship:
        videos = get_video_meta_response_model(api=api, include_relationship=False)
        return api.model('SeriesResponseModel', {
            'id': fields.Integer(required=True),
            'name': fields.String(required=True),
            'rating': fields.Float(required=True),
            'videos' : fields.List(fields.Nested(videos))
        })
    else:
        return api.model('SeriesResponseModel', {
            'id': fields.Integer(required=True)
        })


def get_series_request_model(api):

    videos = get_video_meta_response_model(api=api, include_relationship=False)
    return api.model('SeriesRequestModel', {
        'name': fields.String(required=True),
        'rating': fields.Float(required=True),
        'videos' : fields.List(fields.Nested(videos))
    })


def get_video_meta_response_model(api, include_relationship = True):
    if include_relationship:
        subtitle_model = get_subtitle_model(api)
        star_model = get_star_model(api)
        director_model = get_director_model(api)
        genre_model = get_genre_model(api)
        series_model = get_series_model(api)
        return api.model('VideoMetaResponseModel', {
            'id': fields.Integer(required=True, description='Id'),
            'title': fields.String(required=True),
            'description': fields.String(),
            'file_path': fields.String(required=True),
            'language': fields.String(required=True),
            'duration_seconds': fields.Float(required=True),
            'media_id': fields.Integer(required=True),
            'screen_width': fields.Integer(),
            'screen_height': fields.Integer(),
            'rating': fields.Float(required=True),
            'upload_date': fields.DateTime(required=True),
            'subtitles': fields.List(fields.Nested(subtitle_model)),
            'stars': fields.List(fields.Nested(star_model)),
            'directors': fields.List(fields.Nested(director_model)),
            'genres': fields.List(fields.Nested(genre_model)),
            'series': fields.List(fields.Nested(series_model)),
            })
    else:
        return api.model('VideoMetaResponseModel', {
            'id': fields.Integer(required=True, description='Id')
            })

def get_video_meta_data_request_model(api):
    subtitle_model = get_subtitle_model(api)
    star_model = get_star_model(api)
    director_model = get_director_model(api)
    genre_model = get_genre_model(api)
    series_model = get_series_model(api)
    return api.model('VideoMetaDataRequestModel',{
        'title' : fields.String(required=True),
        'media_id': fields.Integer(required=True),
        'description': fields.String(),
        'language': fields.String(),
        'rating': fields.Float(),
        'subtitles': fields.List(fields.Nested(subtitle_model)),
        'stars': fields.List(fields.Nested(star_model)),
        'directors': fields.List(fields.Nested(director_model)),
        'genres': fields.List(fields.Nested(genre_model)),
        'series': fields.List(fields.Nested(series_model))
    })

def get_video_request_parser(api):
    request_parser = api.parser()
    request_parser.add_argument("genre", type=str, action='split')
    request_parser.add_argument("series", type=str)
    request_parser.add_argument("star", type=str, action='split')
    request_parser.add_argument("director", type=str, action='split')
    request_parser.add_argument("search", type=str)

    request_parser.add_argument("sort_by",type=str, choices=["genre", "star", "director", "title", "duration_seconds", "upload_date", "language"])
    request_parser.add_argument("order", type=str, choices=["asc","desc"], default = "asc" )
    
    request_parser.add_argument("min_duration", type=int)  # e.g., ?min_duration=180
    request_parser.add_argument("max_duration", type=int)

    # TODO: pagination
    # request_parser.add_argument("page", type=int, default=1)
    # request_parser.add_argument("per_page", type=int, default=10)
    return request_parser


def get_user_model(api):
    return api.model('UserModel',{
        'id' : fields.Integer(required=True),
        'user_name' : fields.String(required=True),
        'hashed_password': fields.String(required=True),
        'email': fields.String(required=True),
        'user_type': fields.String(required=True),
        'creation_date': fields.DateTime(required=True)
    })


def get_user_request_model(api):
    return api.model('UserModel',{
        'user_name' : fields.String(required=True),
        'password': fields.String(required=True)
    })


def get_media_task_model(api):
    return api.model('MediaTaskModel',{
        "media_id": fields.Integer(required=True),
        "task_type": fields.String(required=True),
        "status": fields.String(required=True),
        "error_message": fields.String(required=True),
        'creation_date': fields.DateTime(required=True)
    })

def get_media_task_request_model(api):
    return api.model('MediaTaskRequestModel',{
        "media_id": fields.Integer(required=True),
        "task_type": fields.String(required=True),
        "hls_url": fields.String(required=True)
    })