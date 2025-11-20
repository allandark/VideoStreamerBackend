from flask_restx import Namespace, Resource, fields, Model
from flask_jwt_extended import JWTManager
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from flask import send_file, send_from_directory,request
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

jwt = JWTManager()

authorizations = {
    "jsonWebToken":{
        "type": "apiKey",
        "in": "header",
        "name": "Authorization"
    }
}

def create_api_video(app_context):

    api: Namespace = Namespace("video", description="Video namespace for providing HLS video data", authorizations=authorizations)

    # Models
    media_model: Model = api.model('MediaModel', {
        'name': fields.String(required=True, description='Name of video file/dir'),
        'type': fields.String(required=True, description='Type of video file')
        })

    convert_hls_model: Model = api.model("ConvertHLSModel",{
        'name': fields.String(required=True, description='Name of video file/dir')
    })

        
    upload_model = api.model('UploadModel', {
        'name': fields.String(required=True, description='Name of video file/dir'),
        'file': fields.Raw(required=True, description='File to upload', example='file'),
        })

        
    upload_parser = api.parser()
    upload_parser.add_argument('file', location='files',
                            type=FileStorage, required=True,
                            help='File to upload')
    upload_parser.add_argument('name', location='form',
                            type=str, required=True,
                            help='Video name')



    @api.route('/hls')
    class MP4Uploader(Resource):
        @api.doc('Get all mp4 files')
        @api.marshal_list_with(media_model, code=200)
        def get(self):
            return app_context.media_manager.video_get_all()

        # TODO: configurable resolution and such
        @api.doc('Converts the mp4 file to HLS format')
        @api.expect(convert_hls_model)
        def post(self):
            if not app_context.media_manager.upload_file_exists(request.json["name"]):
                return {"error": "mp4 file does not exist, please upload it first"}, 404
            res = app_context.media_manager.video_generate_hls_variants(request.json["name"])
            if not res:
                return {"message": "failed to convert mp4 files"}, 400
            return {"message": "file converted successfully"}, 200

    @api.route('/download/<string:video_name>')
    class MP4Downloader(Resource):
        @api.doc('Upload mp4 file and convert it to HLS format')
        @api.produces(['video/mp4'])
        def get(self, video_name):            
            url = app_context.media_manager.upload_get_file(video_name)
            return send_file(str(url), as_attachment=True, mimetype="video/mp4")

    @api.route('/upload')
    class MP4Uploader(Resource):
        @api.doc('UGet all mp4 files')
        @api.marshal_list_with(media_model, code=200)
        def get(self):
            return app_context.media_manager.upload_get_all()

        @api.doc('Upload mp4 file and convert it to HLS format')
        @api.expect(upload_parser)
        def post(self):
            args = upload_parser.parse_args()
            file = args['file']
            filename = args['name']
            if file is None:
                return {"error": "request contains no file"}, 400
            if filename is None:
                return {"error": "empty filename"}, 400
            filename = secure_filename(filename)
            
            res = app_context.media_manager.upload_save(file=file, filename=filename)
            if not res:
                return {"message": "error saving file"}, 400
            return {"message": "file uploaded successfully"}, 200

    @api.route('/upload/<string:video_name>')
    class MP4UploaderName(Resource):
        ''' Upload mp4 file and convert it to hls
        '''

        @api.doc('Delete video files from storage and remove database entry')
        def delete(self, video_name):
            res = app_context.media_manager.upload_file_exists(video_name)
            res = res or app_context.media_manager.video_file_exists(video_name)      
            if not res:
                return {"error": "file not found"}, 404 
            res = False
            res = app_context.media_manager.upload_remove(video_name)
            res = res or app_context.media_manager.video_remove(video_name)
            if not res:
                return {"error": "failed to delete file"}, 400 
            return {"message": "file deleted successfully"}, 200
                
    @api.route('/playlist/<string:video_name>')
    class HlsPlaylist(Resource):
        ''' Request master HLS playlist file
        '''
        @api.doc('Get HLS playlist master file')
        def get(self, video_name):
            if not app_context.media_manager.video_file_exists(video_name):
                return {"error": "file not found"}, 404  
            url = app_context.media_manager.video_get_file(video_name) 
            return send_file(str(url))

    @api.route('/playlist/<string:video_name>/<string:playlist_id>')
    class HlsPlaylistName(Resource):
        ''' Request specific HLS playlist file
        '''
        @api.doc('Get HLS playlist master file')
        def get(self, video_name, playlist_id):
            if not app_context.media_manager.video_file_exists(video_dir=video_name, file=playlist_id):
                return {"error": "file not found"}, 404  
            url = app_context.media_manager.video_get_file(video_dir=video_name, file=playlist_id) 
            return send_file(str(url))

    @api.route('/chunk/<string:video_name>/<string:chunk_id>')
    class HlsChunk(Resource):
        ''' Request Hls chunk data
        '''
        @api.doc('Get video chunk from video_name with chunk_id file name. Chunk id ex: ')          
        def get(self, video_name, chunk_id):
            if not app_context.media_manager.video_file_exists(video_dir=video_name, file=chunk_id):
                return {"error": "file not found"}, 404    
            url = app_context.media_manager.video_get_file(video_dir=video_name, file=chunk_id)
            return send_file(str(url))

    return api