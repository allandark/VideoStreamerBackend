import logging
logger : logging.Logger = logging.getLogger("app")





# import subprocess
# from pathlib import Path

# def generate_hls(
#         input_file: str, 
#         output_dir: str, 
#         playlist_name: str = "playlist.m3u8", 
#         segment_prefix: str = "playlist"):
#     """
#     Converts an MP4 file into HLS format using ffmpeg.

#     Args:
#         input_file (str): Path to the input MP4 file.
#         output_dir (str): Directory where HLS files will be stored.
#         playlist_name (str): Name of the main playlist file (default: playlist.m3u8).
#         segment_prefix (str): Prefix for segment files (default: playlist).

#     Returns:
#         None
#     """
#     # Ensure output directories exist
#     chunk_dir = Path(output_dir) / "chunk"
#     playlist_dir = Path(output_dir) / "playlist"
#     chunk_dir.mkdir(parents=True, exist_ok=True)
#     playlist_dir.mkdir(parents=True, exist_ok=True)

#     cmd = [
#         "ffmpeg",
#         "-i", input_file,
#         "-codec:", "copy",
#         "-start_number", "0",
#         "-hls_time", "10",
#         "-hls_list_size", "0",
#         "-hls_segment_filename", str(chunk_dir / f"{segment_prefix}%d.ts"),
#         str(playlist_dir / playlist_name)
#     ]


import ffmpeg
from pathlib import Path

def generate_hls_ffmpeg(
        input_file: str, 
        output_dir: str, 
        playlist_name: str = "playlist.m3u8", 
        segment_prefix: str = "playlist"):
    """
    Converts an MP4 file into HLS format using ffmpeg-python.

    Args:
        input_file (str): Path to the input MP4 file.
        output_dir (str): Base directory for HLS output.
        playlist_name (str): Name of the main playlist file.
        segment_prefix (str): Prefix for segment files.
    """
    # Prepare directories
    chunk_dir = Path(output_dir) / "chunk"
    playlist_dir = Path(output_dir) / "playlist"
    chunk_dir.mkdir(parents=True, exist_ok=True)
    playlist_dir.mkdir(parents=True, exist_ok=True)

    # Build HLS output paths
    segment_pattern = str(chunk_dir / f"{segment_prefix}%d.ts")
    playlist_path = str(playlist_dir / playlist_name)

    # Build ffmpeg command
    (
        ffmpeg
        .input(input_file)
        .output(
            playlist_path,
            codec="copy",
            start_number=0,
            hls_time=10,
            hls_list_size=0,
            hls_segment_filename=segment_pattern,
            format="hls"
        )
        .run()
    )

    print(f"HLS playlist created at: {playlist_path}")