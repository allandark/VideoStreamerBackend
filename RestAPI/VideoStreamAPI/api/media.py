from flask_restx import Namespace, Resource, fields, Model
from flask_jwt_extended import JWTManager
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from flask import send_file, send_from_directory,request
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

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

def create_api_media(app_context):

    api: Namespace = Namespace("media", description="Media endpoint for providing HLS video data", authorizations=authorizations)

    # Models
    # media_model: Model = api.model('MediaModel', {
    #     'name': fields.String(required=True, description='Name of video file/dir'),
    #     'type': fields.String(required=True, description='Type of video file')
    #     })

    convert_hls_model: Model = api.model("ConvertHLSModel",{
        'name': fields.String(required=True, description='Name of video file/dir')
    })

        
    upload_model = api.model('UploadModel', {
        'name': fields.String(required=True, description='Name of video file/dir'),
        'file': fields.Raw(required=True, description='File to upload', example='file'),
        })

    
    media_model = api.model('MediaModel',{
        'id' : fields.Integer(required=True, description='Primary key'),
        'name' : fields.String(required=True, description='media name'),
        'mimetype' : fields.String(required=True, description='media type'),
        'hash' : fields.String(required=True, description='file sh265-hash'),
    })


    file_response_schema = api.schema_model('FileResponse', {
        'content': {
            'video/mp4': {
                'schema': {'type': 'string', 'format': 'binary'}
            },
            'image/png': {
                'schema': {'type': 'string', 'format': 'binary'}
            },
            'image/svg+xml': {
                'schema': {'type': 'string', 'format': 'binary'}
            }
        }
    })

    binary_response = api.schema_model('BinaryFile', {'type': 'string', 'format': 'binary'})


        
    upload_parser = api.parser()
    upload_parser.add_argument('file', location='files',
                            type=FileStorage, required=True,
                            help='File to upload')
    upload_parser.add_argument('name', location='form',
                            type=str, required=True,
                            help='Video name')


    @api.route('/download/<int:id>')
    class MP4Downloader(Resource):

        @api.doc(
            description='Download media file',
            responses={200: ('File downloaded', binary_response)})   
        @api.produces(['application/octet-stream'])
        def get(self, id):            
            meta_data = app_context.db_context.media.Get(id)
            if meta_data is None:
                return None, 400
            url = app_context.media_manager.uploader.GetFileUrl(hash=meta_data['hash'], mimetype=meta_data['mimetype'])
            return send_file( url,  as_attachment=True)

    @api.route('/upload')
    class MP4Uploader(Resource):
        @api.doc('Get all media files meta data')
        @api.marshal_list_with(media_model, code=200)
        def get(self):
            return app_context.db_context.media.GetAll()

        @api.doc('Upload media file and store metadata in db')
        @api.expect(upload_parser)
        @api.marshal_with(media_model)
        def post(self):
            # Parse args
            args = upload_parser.parse_args()
            file = args['file']
            filename = args['name']
            if file is None:
                return None, 400
            if filename is None:
                return None, 400
            filename = secure_filename(filename)    

            # Check for dublicate and save
            media = app_context.db_context.media.GetAttr("name", filename)
            if media:
                return None, 400
            res = app_context.media_manager.uploader.FileSave(file=file, filename=filename)     
            if not res:
                return None, 400
            
            media = app_context.db_context.media.Create({
                "hash" : res['hash'],
                "mimetype" : res['type'],
                "name" : res['file_name']
            })
            return media, 201

    @api.route('/thumbnail/<int:media_id>')
    class MP4UploaderName(Resource):
        ''' Returns thumbnail of media
        '''

        @api.doc('Retur')
        def get(self, media_id):
            media = app_context.db_context.media.Get(media_id)
            if media is None:
                return {"error": "media not found"}, 404
            dir = app_context.media_manager.video_manager.GetDir(media['hash'])                
            return send_from_directory(dir, "out_thumbnail.png", mimetype='image/png')
                
    @api.route('/playlist/<int:media_id>')
    class HlsPlaylist(Resource):
        ''' Request master HLS playlist file
        '''
        @api.doc('Get HLS playlist master file')
        def get(self, media_id):
            
            media = app_context.db_context.media.Get(media_id)
            if media is None:
                return {"error": "file not found"}, 404  
        
            dir = app_context.media_manager.video_manager.GetDir(media['hash'])
            return send_from_directory(dir,  "out_master.m3u8", mimetype='application/vnd.apple.mpegurl')

    @api.route('/playlist/<int:media_id>/<string:file_name>')
    class HlsPlaylistName(Resource):
        ''' Request specific HLS playlist file
        '''
        @api.doc('Get HLS playlist master file')
        def get(self, media_id, file_name):
            media = app_context.db_context.media.Get(media_id)
            if media is None:
                return None, 404
            dir = app_context.media_manager.video_manager.GetDir(media['hash'])
            return send_from_directory(dir, file_name, mimetype='application/vnd.apple.mpegurl')

    @api.route('/chunk/<int:media_id>/<string:file_name>')
    class HlsChunk(Resource):
        ''' Request Hls chunk data
        '''
        @api.doc('Get video chunk from video_name with chunk_id file name. Chunk id ex: ')          
        def get(self, media_id, file_name):
            media = app_context.db_context.media.Get(media_id)
            if media is None:
                return None, 404
            dir = app_context.media_manager.video_manager.GetDir(media['hash'])
            return send_from_directory(dir, file_name, mimetype='video/MP2T')

    return api