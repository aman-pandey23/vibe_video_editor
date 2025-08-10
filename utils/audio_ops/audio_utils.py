from pathlib import Path
from moviepy.editor import AudioFileClip, VideoFileClip

def extract_audio_from_video(video_path: str, output_audio_path: str) -> str:
    """
    Extract audio from a video and save as MP3.
    """
    video_path = Path(video_path)
    output_audio_path = Path(output_audio_path)

    clip = VideoFileClip(str(video_path))
    if clip.audio is None:
        clip.close()
        raise ValueError(f"No audio track found in {video_path}")
    
    output_audio_path.parent.mkdir(parents=True, exist_ok=True)
    clip.audio.write_audiofile(str(output_audio_path))
    clip.close()
    return str(output_audio_path)


def overlay_audio_on_video(video_path: str, audio_path: str, output_path: str) -> str:
    """
    Overlay an audio file onto a video and save new video.
    Audio is trimmed or looped to match video length.
    """
    video_path = Path(video_path)
    audio_path = Path(audio_path)
    output_path = Path(output_path)

    video = VideoFileClip(str(video_path))
    audio = AudioFileClip(str(audio_path))

    # Match lengths
    if audio.duration > video.duration:
        audio = audio.subclip(0, video.duration)
    elif audio.duration < video.duration:
        loops = int(video.duration // audio.duration) + 1
        audio = audio.audio_loop(duration=video.duration)

    video = video.set_audio(audio)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    video.write_videofile(str(output_path), codec="libx264", audio_codec="aac", fps=video.fps)

    video.close()
    audio.close()
    return str(output_path)
