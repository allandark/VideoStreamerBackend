import ffmpeg
# import subprocess
import sys
import os
# import webvtt
from pathlib import Path
import logging
logger : logging.Logger = logging.getLogger("app")
import shutil
from .hls_builder import HLSBuilder




class VideoMeta:
  def __init__(self, input_file: str, output_dir: str):
    self.input_file = input_file 
    self.output_dir = output_dir
    # self.extract_dir = extract_dir
    filename = str(self.input_file.name).split('.')[0]
    self.output_target_dir = self.output_dir / filename
    

    # Meta data
    self.format = {}
    self.video_tracks = []
    self.audio_tracks = []
    self.subtitle_tracks = []

    self.get_meta_data()
    


  def get_meta_data(self):
    try:
      probe = ffmpeg.probe(self.input_file)
      self.format['bit_rate'] = probe['format']['bit_rate']
      self.format['size'] = probe['format']['size']
      self.format['duration'] = probe['format']['duration']
      self.format['format_name'] = probe['format']['format_name']


      video_track_id = 0
      audio_track_id = 0
      sub_track_id = 0
      for stream in probe['streams']:
        if stream['codec_type'] == 'video':
          video_track = {}
          video_track['codec_name'] = stream['codec_name']
          video_track['codec_long_name'] = stream['codec_long_name']
          video_track['width'] = stream['width']
          video_track['height'] = stream['height']
          video_track['display_aspect_ratio'] = stream['display_aspect_ratio']
          video_track['avg_frame_rate'] = stream['avg_frame_rate']
          video_track['duration'] = stream['duration']
          video_track['track_id'] = video_track_id
          video_track['index'] = stream['index']
          self.video_tracks.append(video_track)
          video_track_id = video_track_id + 1
        elif stream['codec_type'] == 'audio':
          audio_track = {}
          audio_track['codec_name'] = stream['codec_name']
          audio_track['codec_long_name'] = stream['codec_long_name']
          audio_track['sample_fmt'] = stream['sample_fmt']
          audio_track['sample_rate'] = stream['sample_rate']
          audio_track['channels'] = stream['channels']
          audio_track['channel_layout'] = stream['channel_layout']
          audio_track['language'] = stream['tags'].get("language", "Unknown")
          audio_track['title'] = stream['tags'].get("title", "Unknown")
          audio_track['duration'] = stream['duration']
          audio_track['track_id'] = audio_track_id
          audio_track['index'] = stream['index']
          self.audio_tracks.append(audio_track)
          audio_track_id = audio_track_id + 1
        elif stream['codec_type'] == 'subtitle':
          subtitle_track = {}
          subtitle_track['codec_name'] = stream['codec_name']
          subtitle_track['codec_long_name'] = stream['codec_long_name']
          subtitle_track['language'] = stream['tags'].get("language", "Unknown")
          subtitle_track['duration'] = stream['duration']
          subtitle_track['track_id'] = sub_track_id
          subtitle_track['index'] = stream['index']
          self.subtitle_tracks.append(subtitle_track)
          sub_track_id = sub_track_id + 1
    
          
        
      logger.info(f"Video file \"{self.input_file}\" read successfully")
      
    except ffmpeg.Error as e:
      logger.error(e.stderr.decode('utf-8'), file=sys.stderr)


  def __repr__(self):
    return "".join( [f"VideoMeta(input_file={self.input_file}, ",
            f"duration={self.format['duration']}, width={self.video_tracks[0]['width']}, ",
            f"height={self.video_tracks[0]['height']}, codec={self.video_tracks[0]['codec_name']})" ])


class VideoManager:
  def __init__(self, output_dir, upload_dir):
    self.output_dir = output_dir
    self.upload_dir = upload_dir


  def DirExists(self, dir):
    url = self.output_dir / dir
    return os.path.exists(url)

  def DirRemove(self , dir):
    try:
        shutil.rmtree(self.output_dir / dir)      
        logger.info(f"HLS files deleted successfully")      
        return True
    except Exception as e: 
        logger.error(f"Failed to delete HLS files: {e}")
        return False  

  def CreateHls(self, video_data, video_name, **kwargs):
    try:
      
      output_path = self.output_dir / video_name
      logger.debug(f"Creating dir for videos: \"{output_path}\"")
      output_path.mkdir(parents=True, exist_ok=True)

      builder = HLSBuilder(video_data, **kwargs)

      # Add video variants
      if video_data.video_tracks[0]['height'] >= 128:        
        builder.add_video_track("240p", exclude_audio=True)
      if video_data.video_tracks[0]['height'] >= 480:
        builder.add_video_track("480p", exclude_audio=True)
      if video_data.video_tracks[0]['height'] >= 720:
        builder.add_video_track("720p", exclude_audio=True)
      if video_data.video_tracks[0]['height'] >= 1080:
        builder.add_video_track("1080p", exclude_audio=True)
      
      if len(builder.video_tracks) == 0:
        logger.error(f"Video has no valid video tracks")
        return False

      # Build audio tracks
      for track in video_data.audio_tracks:
        builder.add_audio_track(name = "English", id=track['track_id'])

      for track in video_data.subtitle_tracks:
        builder.add_subtitle_track(name = "English", id=track['track_id'])

      # Create thumbnail
      gen_thumbnail: bool = kwargs.get("thumbnail", True)      
      if gen_thumbnail:
        thumbnail_width: bool = kwargs.get("thumbnail_width", 240)
        thumbnail_time: bool = kwargs.get("thumbnail_time", 10)
        builder.add_thumbnail(time=thumbnail_time, width=thumbnail_width)

      builder.add_master()

      res = builder.build()
      return res
    except Exception as e:
      logger.error(f"Failed to create HLS data: {e}")
      return False

  def LoadData(self, input_file):
    input_dir = self.upload_dir / input_file
    vid = VideoMeta(input_dir, self.output_dir)
    return vid

  def GetFile(self, video_dir, file_name):
    return  self.output_dir / video_dir / file_name

  def GetDir(self, video_dir):
    return self.output_dir / video_dir