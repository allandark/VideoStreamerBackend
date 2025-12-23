import ffmpeg
from datetime import datetime
import asyncio
import logging
logger: logging.Logger = logging.getLogger("app")


class HLSBuilder:
    """_summary_
    Builder class for creating hls files with different configurations encapsulating ffmpeg
    """

    def __init__(self, video, **kwargs):

        self.thumbnail: dict[str, str] = {}
        self.master: dict[str, str] = {}
        self.video_tracks: list[dict[str, str]] = []
        self.audio_tracks: list[dict[str, str]] = []
        self.subtitle_tracks: list[dict[str, str]] = []

        # config
        self.video = video
        self.output_prefix = kwargs.get("output_prefix", "out")
        self.hls_time = kwargs.get("hls_time", 10)
        self.hls_segment_prefix = kwargs.get("hls_segment_prefix", "segment")
        self.hls_segment_base_url = kwargs.get("hls_segment_base_url", None)
        self.hls_playlist_base_url = kwargs.get("hls_playlist_base_url", None)
        self.video_time = kwargs.get("video_time", 0)

        self.video_variants: list[dict[str, str]] = [
            {"bandwidth_ffmpeg": "400k", "bandwidth": 400000,
                "resolution": "426x240", "name": "240p"},
            {"bandwidth_ffmpeg": "800k", "bandwidth": 800000,
             "resolution": "854x480", "name": "480p"},
            {"bandwidth_ffmpeg": "1400k", "bandwidth": 1400000,
             "resolution": "1280x720", "name": "720p"},
            {"bandwidth_ffmpeg": "2800k", "bandwidth": 2800000,
             "resolution": "1920x1080", "name": "1080p"},
        ]

        self.LOG_LENGTH = 5000

    def add_video_track(self, resolution: str, exclude_audio: bool = False, id: int = 0):
        """ _summary_\n
        Add video variant track with given resolution

        Args:
            resolution (str): resolution name: \"240p\", \"480p\", \"720p\", \"1080p\"
            exclude_audio (bool, optional): exclude audio in video track. Defaults to False.
        """
        for variant in self.video_variants:
            if resolution == variant['name']:
                uri = f"{self.output_prefix}_{variant['name']}.m3u8"
                if self.hls_playlist_base_url:
                    uri = f"{self.hls_playlist_base_url}{uri}"
                variant['exclude_audio'] = exclude_audio
                variant['uri'] = uri
                variant['track_id'] = id
                self.video_tracks.append(variant)

    def add_audio_track(self, name: str, language: str = "", id: int = 0):
        """ _summary_\n
        Add audio track

        Args:
            name (str): track name
            language (str, optional): short form langauge ex: \"eng\". Defaults to "".
            id (int, optional): stream id. Defaults to 0.
        """
        track_found = False
        for a_track in self.video.audio_tracks:
            if a_track['language'] == language:

                uri = f"{self.output_prefix}_audio_{a_track['language']}.m3u8"
                if self.hls_playlist_base_url:
                    uri = f"{self.hls_playlist_base_url}{uri}"

                self.audio_tracks.append({
                    "track_id": a_track['track_id'],
                    "name": name,
                    "language": a_track['language'],
                    "uri": uri
                })
                track_found = True

        if not track_found:
            uri = f"{self.output_prefix}_audio_{a_track['language']}.m3u8"
            if self.hls_playlist_base_url:
                uri = f"{self.hls_playlist_base_url}{uri}"
            self.audio_tracks.append({
                "track_id": id,
                "name": name,
                "language": self.video.audio_tracks[id]['language'],
                "uri": uri
            })

    def add_subtitle_track(self, name: str, language: str = "", id: int = 0, file: str | None = None):
        """ _summary_\n
        Add subtitle track to video

        Args:
            name (str): name of track
            language (str, optional): short form of language ex. \"eng\" for english. Defaults to "".
            id (int, optional): streamid if video contains builtin subtitle stream. Defaults to 0.
            file (str, optional): external subtitle file, needs to be webvtt compatible. Defaults to None.
        """
        track_found = False
        for s_track in self.video.subtitle_tracks:
            if s_track['language'] == language:
                uri = f"{self.output_prefix}_subs_{s_track['language']}.m3u8"
                if self.hls_playlist_base_url:
                    uri = f"{self.hls_playlist_base_url}{uri}"
                track = {
                    "track_id": s_track['track_id'],
                    "name": name,
                    "language": s_track['language'],
                    "uri": uri
                }
                if file:
                    track['file'] = file
                self.subtitle_tracks.append(track)
                track_found = True

        if not track_found:
            uri = f"{self.output_prefix}_subs_{s_track['language']}.m3u8"
            if self.hls_playlist_base_url:
                uri = f"{self.hls_playlist_base_url}{uri}"
            track = {
                "track_id": id,
                "name": name,
                "language": self.video.subtitle_tracks[id]['language'],
                "uri": uri
            }
            if file:
                track['file'] = file
            self.subtitle_tracks.append(track)

    def add_thumbnail(self, time: float = 0.1, width: int = 120):
        """add a thumbnail png to be created at time with width

        Args:
            time (float, optional): time in video. Defaults to 0.1.
            width (int, optional): width of image, keeps aspect ratio. Defaults to 120.
        """
        self.thumbnail['time'] = time
        self.thumbnail['width'] = width

    def add_master(self, file_name="master"):
        """ _summary_\n
        Adds master playlist file to be build

        Args:
            file_name (str, optional): _description_. Defaults to "master".
        """
        if 'file_name' in self.master:
            return
        self.master['file_name'] = file_name

    def build(self):
        """ _summary_\n
        Performs the build with the current configuration provided by the previous add commands
        Returns:
            res (dict[str, any])': _description_. Dictionary containing status and configuration data
        """
        result = asyncio.run(self.build_async())
        return result

    async def build_async(self):
        tasks = {}
        build_status = True

        logger.info(f"Building HLS...")

        if 'time' in self.thumbnail:
            logger.debug(f"Thumbnail task")
            tasks['thumbnail'] = asyncio.create_task(
                self._build_thumbnail(self.thumbnail))

        for video_track in self.video_tracks:
            logger.debug(f"Video task: {video_track['name']}")
            tasks[f"vid_{video_track['name']}"] = asyncio.create_task(
                self._build_video_track(video_track=video_track, time=self.video_time))

        for audio_track in self.audio_tracks:
            logger.debug(f"Audio task: {audio_track['name']}")
            tasks[f"au_{audio_track['name']}"] = asyncio.create_task(
                self._build_audio_track(audio_track=audio_track, time=self.video_time))

        for sub_track in self.subtitle_tracks:
            logger.debug(f"Sub task: {sub_track['name']}")
            tasks[f"sub_{sub_track['name']}"] = asyncio.create_task(
                self._build_subtitle_track(subtitle_track=sub_track, time=self.video_time))

        logger.debug("Fire tasks")
        results = await asyncio.gather(*tasks.values())
        build_status = all(results)

        if 'file_name' in self.master:
            logger.debug("Building master")
            self._build_master(self.master, self.video_tracks,
                               self.audio_tracks, self.subtitle_tracks)

        logger.info(
            f"HLS builder done, status: {build_status}, output: \"{self.output_prefix}\"")

        return {
            "build_status": build_status,
            "build_date": datetime.now().isoformat(),
            "output_prefix": self.output_prefix,
            "hls_time": self.hls_time,
            "hls_segment_prefix": self.hls_segment_prefix,
            "hls_playlist_base_url": self.hls_playlist_base_url,
            "hls_segment_base_url": self.hls_segment_base_url,
            "master": self.master,
            "thumbnail": self.thumbnail,
            "video_tracks": self.video_tracks,
            "audio_tracks": self.audio_tracks,
            "subtitle_tracks": self.subtitle_tracks,
        }

    async def _build_video_track(self, video_track, time=0):

        output_file = f"{self.video.output_target_dir}/{self.output_prefix}_{video_track['name']}.m3u8"
        segment_file = f"{self.video.output_target_dir}/{self.output_prefix}_{video_track['name']}_%03d.ts"
        input_kwargs = {}
        if time != 0:
            input_kwargs['t'] = time

        output_kwargs = {
            "vcodec": self.video.video_tracks[video_track['track_id']]['codec_name'],
            "video_bitrate":  video_track['bandwidth_ffmpeg'],
            "f": "hls",
            "hls_time": self.hls_time,
            "hls_list_size": 0,
            "hls_segment_filename": segment_file,
            "preset": "fast"
        }
        if video_track['exclude_audio']:
            output_kwargs['an'] = None
        else:
            output_kwargs['acodec'] = "copy"
            output_kwargs['map'] = f"0:a"

        if self.hls_segment_base_url:
            output_kwargs['hls_base_url'] = self.hls_segment_base_url
        logger.debug(f"ffmpeg args: {output_kwargs}")
        try:
            process = (
                ffmpeg
                .input(self.video.input_file, **input_kwargs)
                .filter('scale', -2, video_track['name'][:-1])
                .output(output_file, **output_kwargs)
                .overwrite_output()
                .run_async(pipe_stdout=True, pipe_stderr=True)
            )
            loop = asyncio.get_running_loop()
            stdout, stderr = await loop.run_in_executor(
                None,
                process.communicate
            )
            if stdout:
                logger.debug(stdout.decode(errors="ignore")[:500])

            if process.returncode != 0:
                raise RuntimeError(
                    f"FFmpeg failed for {video_track['name']}:\n{stderr.decode(errors='ignore')[:500]}"
                )

            return True
        except ffmpeg.Error as e:
            logger.error(e.stderr.decode('utf-8'))
            return False

    async def _build_audio_track(self, audio_track, time=0):
        track = self.video.audio_tracks[audio_track['track_id']]
        output_file = f"{self.video.output_target_dir}/{self.output_prefix}_audio_{track['language']}.m3u8"
        segment_file = f"{self.video.output_target_dir}/{self.output_prefix}_audio_{track['language']}_%03d.ts"
        input_kwargs = {

        }
        if time != 0:
            input_kwargs['t'] = time

        output_kwargs = {
            "acodec": track['codec_name'],
            "audio_bitrate":  "128k",
            "map": f"0:a:{track['track_id']}",
            "ar":  track['sample_rate'],
            "f": "hls",
            "hls_time": self.hls_time,
            "hls_list_size": 0,
            "hls_segment_filename": segment_file,
        }

        if self.hls_segment_base_url:
            output_kwargs['hls_base_url'] = self.hls_segment_base_url
        logger.debug(f"ffmpeg args: {output_kwargs}")
        try:
            process = (
                ffmpeg
                .input(self.video.input_file, **input_kwargs)
                .output(output_file, **output_kwargs)
                .overwrite_output()
                .run_async(pipe_stdout=True, pipe_stderr=True)
            )
            loop = asyncio.get_running_loop()
            stdout, stderr = await loop.run_in_executor(
                None,
                process.communicate
            )
            if stdout:
                logger.debug(stdout.decode(errors="ignore")[:self.LOG_LENGTH])

            if process.returncode != 0:
                raise RuntimeError(
                    f"FFmpeg failed for {audio_track['name']}:\n{stderr.decode(errors='ignore')[:self.LOG_LENGTH]}"
                )
            return True
        except ffmpeg.Error as e:
            logger.error(e.stderr.decode('utf-8'))
            return False

    async def _build_thumbnail(self, thumbnail_dict):

        out_filename = f"{self.video.output_target_dir}/{self.output_prefix}_thumbnail.png"
        try:
            process = (
                ffmpeg
                .input(self.video.input_file, ss=thumbnail_dict['time'])
                .filter('scale', thumbnail_dict['width'], -1)
                .output(out_filename, vframes=1, update=1)
                .overwrite_output()
                .run_async(pipe_stdout=True, pipe_stderr=True)
            )
            loop = asyncio.get_running_loop()
            stdout, stderr = await loop.run_in_executor(
                None,
                process.communicate
            )
            if stdout:
                logger.debug(stdout.decode(errors="ignore")[:self.LOG_LENGTH])

            if process.returncode != 0:
                raise RuntimeError(
                    f"FFmpeg failed for thumbnail:\n{stderr.decode(errors='ignore')[:self.LOG_LENGTH]}"
                )
            return True
        except ffmpeg.Error as e:
            logger.error(e.stderr.decode('utf-8'))
            return False

    async def _build_subtitle_track(self, subtitle_track, time=0):
        track = self.video.subtitle_tracks[subtitle_track['track_id']]
        output_file = f"{self.video.output_target_dir}/{self.output_prefix}_subs_{track['language']}.m3u8"
        segment_file = f"{self.video.output_target_dir}/{self.output_prefix}_subs_{track['language']}_%03d.ts"
        input_kwargs = {

        }
        if time != 0:
            input_kwargs['t'] = time

        output_kwargs = {
            "scodec": "webvtt",  # track['codec_name'],
            "map": f"0:s:{track['track_id']}",
            "f": "hls",
            "hls_time": self.hls_time,
            "hls_list_size": 0,
            "hls_segment_filename": segment_file,
        }

        if self.hls_segment_base_url:
            output_kwargs['hls_base_url'] = self.hls_segment_base_url
        logger.debug(f"ffmpeg args: {output_kwargs}")
        try:
            process = (
                ffmpeg
                .input(self.video.input_file, **input_kwargs)
                .output(output_file, **output_kwargs)
                .overwrite_output()
                .run_async(pipe_stdout=True, pipe_stderr=True)
            )

            loop = asyncio.get_running_loop()
            stdout, stderr = await loop.run_in_executor(
                None,
                process.communicate
            )
            if stdout:
                logger.debug(stdout.decode(errors="ignore")[:self.LOG_LENGTH])

            if process.returncode != 0:
                raise RuntimeError(
                    f"FFmpeg failed for {subtitle_track['name']}:\n{stderr.decode(errors='ignore')[:self.LOG_LENGTH]}"
                )
            return True
        except ffmpeg.Error as e:
            logger.error(e.stderr.decode('utf-8'))
            return False

    def _build_master(self, master_dict, video_tracks, audio_tracks=None, subtitle_tracks=None):
        output_file = f"{self.video.output_target_dir}/{self.output_prefix}_{master_dict['file_name']}.m3u8"
        lines = []
        lines.append("#EXTM3U")
        lines.append("#EXT-X-VERSION:3\n")

        for audio_track in audio_tracks:
            default_str = "YES" if audio_track.get("default", False) else "NO"
            lines.append(
                f'#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="audio",NAME="{audio_track["name"]}",'
                f'LANGUAGE="{audio_track["language"]}",DEFAULT={default_str},AUTOSELECT=YES,URI="{audio_track["uri"]}"'
            )
        lines.append("")

        for sub_track in subtitle_tracks:
            default_str = "YES" if sub_track.get("default", False) else "NO"
            lines.append(
                f'#EXT-X-MEDIA:TYPE=SUBTITLES,GROUP-ID="subs",NAME="{sub_track["name"]}",'
                f'LANGUAGE="{sub_track["language"]}",DEFAULT={default_str},AUTOSELECT=YES,URI="{sub_track["uri"]}"'
            )
        lines.append("")

        for v in video_tracks:
            audio_ref = 'AUDIO="audio"' if audio_tracks else ""
            subs_ref = 'SUBTITLES="subs"' if subtitle_tracks else ""

            ref_parts = ", ".join([x for x in [audio_ref, subs_ref] if x])

            if ref_parts:
                ref_parts = "," + ref_parts

            lines.append(
                f'#EXT-X-STREAM-INF:BANDWIDTH={v["bandwidth"]},RESOLUTION={v["resolution"]}{ref_parts}'
            )
            lines.append(v["uri"])
            lines.append("")

        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
