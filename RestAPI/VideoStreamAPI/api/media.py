from flask_restx import Namespace, Resource, fields, Model
from flask_jwt_extended import JWTManager
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from flask import send_file, send_from_directory,request
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from VideoStreamAPI.api.api_models import get_media_task_model, get_media_task_request_model
from VideoStreamAPI.core.media_manager import TaskType, TaskStatus

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

    upload_chunk_model = api.model('UploadChunkModel',{
        "task_id": fields.String(required=True, description="ID of the upload task"),
        "chunk_index": fields.Integer(required=True),
        "chunk_data": fields.String(required=True, description="Binary file part")
    })

    complete_chunk_model = api.model('CompleteChunkModel',{
        "task_id" : fields.String(required=True, description="ID of the upload task")
    })
    
    # binary_response = api.schema_model('BinaryFile', {'type': 'string', 'format': 'binary'})

    upload_parser = api.parser()
    upload_parser.add_argument('file', location='files',
                            type=FileStorage, required=True,
                            help='File to upload')
    upload_parser.add_argument('name', location='form',
                            type=str, required=True,
                            help='Video name')

    media_task_model = get_media_task_model(api)
    media_task_request_model = get_media_task_request_model(api)

    media_model = api.model('MediaModel',{
        'id' : fields.Integer(required=True, description='Primary key'),
        'name' : fields.String(required=True, description='media name'),
        'mimetype' : fields.String(required=True, description='media type'),
        'hash' : fields.String(required=True, description='file sh265-hash'),
        'master_file': fields.Boolean(required=True),
        'video_tracks': fields.Raw(required=True),
        'audio_tracks': fields.Raw(required=True),
        'subtitle_tracks': fields.Raw(required=True),
        'tasks' : fields.List(fields.Nested(media_task_model))
    })

    media_request_model = api.model('MediaModel',{
        'name' : fields.String(required=True, description='media name'),
    })

    @api.route('/task')
    class Task(Resource):
        @api.doc(description="Returns all tasks in database")
        @api.marshal_list_with(media_task_model)
        def get(self):
            tasks = app_context.db_context.tasks.GetAll()
            return tasks, 200

        @api.doc(description="Start new task")
        @api.expect(media_task_request_model)
        @api.marshal_with(media_task_model)
        def post(self):
            media_id = request.json.get('media_id', 0)
            task_type = request.json['task_type']
            params = request.json.get('params',{})
            logger.debug(f"media_id: {media_id}, task: {task_type}, params: {params}")

            queue = False if task_type == TaskType.FILE_REASSEMBLY else True
            task = app_context.media_manager.AddOrUpdateTask(
                type=task_type,
                media_id=media_id,
                queue_task=queue,
                **params
                )
            if task is None:
                return task, 400
            return task, 201
            

    @api.route('/task/<int:id>')
    class Task(Resource):
        @api.doc(description="Get task by id from database")
        @api.marshal_with(media_task_model)
        def get(self, id):
            task = app_context.db_context.tasks.Get(id)
            if task is None:
                return None, 404
            return task, 200

        @api.doc(description="Delete task by id from database")
        def delete(self, id):
            task = app_context.db_context.tasks.Get(id)
            if task is None:
                return None, 404
            res = app_context.db_context.tasks.Delete(id)
            if not res:
                return {"error": "could not delete task"}, 500
            return {"message": "task deleted successfully"}, 200

    # @api.route('/download/<int:id>')
    # class MP4Downloader(Resource):

    #     @api.doc(
    #         description='Download media file',
    #         responses={200: ('File downloaded', binary_response)})   
    #     @api.produces(['application/octet-stream'])
    #     def get(self, id):            
    #         meta_data = app_context.db_context.media.Get(id)
    #         if meta_data is None:
    #             return None, 400
    #         url = app_context.media_manager.uploader.GetFileUrl(hash=meta_data['hash'], mimetype=meta_data['mimetype'])
    #         return send_file( url,  as_attachment=True)

    @api.route('')
    class Media(Resource):
        @api.doc('Get all media files meta data')
        @api.marshal_list_with(media_model, code=200)
        def get(self):
            return app_context.db_context.media.GetAll()
        
    @api.route('/<int:id>')
    class MediaId(Resource):
        @api.doc('Get all media files meta data')
        @api.marshal_list_with(media_model, code=200)
        def get(self, id):
            media = app_context.db_context.media.Get(id)
            if media is None:
                return None, 404
            return media
        
        @api.doc(description="Delete media by id from database")
        def delete(self, id):
            task = app_context.db_context.media.Get(id)
            if task is None:
                return None, 404
            res = app_context.db_context.media.Delete(id)
            if not res:
                return {"error": "could not delete media"}, 500
            return {"message": "media deleted successfully"}, 200


    @api.route('/upload/chunk_complete')
    class UploadChunkComplete(Resource):
        @api.doc(description='Complete chunk upload')
        @api.expect(complete_chunk_model)
        @api.marshal_with(media_task_model)
        def post(self):
            task_id = int(request.json["task_id"])
            task = app_context.db_context.tasks.Get(task_id)

            if len(task["params"]["received_chunks"]) != task["params"]["chunk_count"]:
                logger.error(f"not all chunks uploaded")
                return {"error": "Not all chunks uploaded"}, 400
            
            app_context.media_manager.AddOrUpdateTask(
                type= task['task_type'],
                media_id = task['media_id'],
                task_id = task_id,
                queue_task = True                
            )

    @api.route('/upload/chunk_upload')
    class UploadChunk(Resource):
        @api.doc(description='Upload chunk file')
        @api.expect(upload_chunk_model)
        @api.marshal_with(media_task_model)
        def post(self):
            task_id = int(request.form["task_id"])
            chunk_index = int(request.form["chunk_index"])
            chunk_file = request.files["chunk_data"]

            task = app_context.db_context.tasks.Get(task_id)
            if task is None:
                return None, 404
            if task['status'] != TaskStatus.PENDING:
                logger.warning(f"Cannot upload chunks without a valid task")
                return None, 400
            
            app_context.media_manager.uploader.ChunkSave(task_id, chunk_index, chunk_file)
            task['params']['received_chunks'][chunk_index] = True
            app_context.media_manager.AddOrUpdateTask(
                type= task['task_type'],
                media_id = task['media_id'],
                task_id = task_id,
                queue_task = False,
                **task['params']                               
            )
            return task, 200

    @api.route('/upload')
    class MediaUploader(Resource):

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

    @api.route('/hls/thumbnail/<int:media_id>')
    class Thumbnail(Resource):
        ''' Returns thumbnail of media
        '''
        @api.doc('Retur')
        def get(self, media_id):
            media = app_context.db_context.media.Get(media_id)
            if media is None:
                return {"error": "media not found"}, 404
            dir = app_context.media_manager.video_manager.GetDir(media['hash'])                
            return send_from_directory(dir, "out_thumbnail.png", mimetype='image/png')
                
    @api.route('/hls/playlist/<int:media_id>')
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

    @api.route('/hls/playlist/<int:media_id>/<string:file_name>')
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

    @api.route('/hls/chunk/<int:media_id>/<string:file_name>')
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