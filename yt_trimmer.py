import subprocess
from uuid import uuid4
import os
import whisper
from datetime import datetime, timedelta
from flask import Flask, jsonify, request

app = Flask(__name__)

# Global scope
MODEL = whisper.load_model("base")

def cut_youtube_segment(url: str, start_time: str, duration: str):
    ffmpeg_path = './ffmpeg/bin/ffmpeg.exe'
    filename = f"clip_{uuid4().hex[:8]}.mp4"
    full_path = os.path.abspath(filename)

    result = {
        "success": False,
        "url": url,
        "start_time": start_time,
        "duration": duration,
        "file_name": filename,
        "file_path": full_path,
        "error": None
    }

    try:
        stream_url = subprocess.check_output(
            ['yt-dlp', '-f', 'best', '-g', url],
            text=True
        ).strip()

        subprocess.run([
            ffmpeg_path,
            '-ss', start_time,
            '-i', stream_url,
            '-t', duration,
            '-c', 'copy',
            '-y',
            full_path
        ], check=True)

        result["success"] = True
        return result

    except subprocess.CalledProcessError as e:
        result["error"] = str(e)
        return result

def transcribe_video_clip(video_path: str, model_size="base"):
    print(f"Loading Whisper model: {model_size}")
    try:

        ffmpeg_dir = os.path.abspath("ffmpeg/bin")
        os.environ["PATH"] += os.pathsep + ffmpeg_dir

        print("Transcribing audio...")
        result = MODEL.transcribe(video_path, language="hi")
        print("Transcription complete.")
        return {
            "text": result.get("text", ""),
            "segments": result.get("segments", []),
            "language": result.get("language", "unknown")
        }
    except Exception as e:
        print(f"Whisper error: {e}")
        return {"text": "", "segments": [], "language": "error"}


def time_str_to_seconds(t: str):
    """Convert 'HH:MM:SS' to total seconds."""
    h, m, s = map(int, t.split(':'))
    return h * 3600 + m * 60 + s

def seconds_to_time_str(seconds: int):
    """Convert seconds to 'HH:MM:SS' format."""
    return str(timedelta(seconds=seconds))

def main(url: str, start_time: str, duration: str, chunk_length=10):
    start_seconds = time_str_to_seconds(start_time)
    total_duration = time_str_to_seconds(duration)

    # Step 1: Download full segment once
    cut_result = cut_youtube_segment(url, start_time, duration)
    if not cut_result["success"]:
        print(f"Error cutting full video segment: {cut_result['error']}")
        return []

    full_video_path = cut_result["file_path"]
    transcript_results = []

    # Step 2: Process full clip in 20-second segments
    for offset in range(0, total_duration, chunk_length):
        chunk_start = start_seconds + offset
        chunk_dur = min(chunk_length, total_duration - offset)

        chunk_start_str = seconds_to_time_str(offset)  # relative to start of clip
        chunk_dur_str = seconds_to_time_str(chunk_dur)

        print(f"Processing segment {chunk_start_str} to {seconds_to_time_str(offset + chunk_dur)}")

        # Use ffmpeg to cut chunk from downloaded full video
        from uuid import uuid4
        import subprocess

        chunk_file = f"chunk_{uuid4().hex[:8]}.mp4"
        subprocess.run([
            './ffmpeg/bin/ffmpeg.exe',
            '-ss', chunk_start_str,
            '-i', full_video_path,
            '-t', chunk_dur_str,
            '-c', 'copy',
            '-y',
            chunk_file
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Transcribe the chunk
        whisper_result = transcribe_video_clip(chunk_file)

        if whisper_result["text"]:
            transcript_results.append({
                "start_time": seconds_to_time_str(chunk_start),
                "text": whisper_result["text"]
            })
            print(f"Transcribed chunk [{chunk_start_str}]: {whisper_result['text']}")
        else:
            print(f"No transcription for chunk starting at {chunk_start_str}")

        # Cleanup chunk
        if os.path.exists(chunk_file):
            os.remove(chunk_file)

    # Cleanup full video
    if os.path.exists(full_video_path):
        os.remove(full_video_path)

    # Print all results
    print("\n--- Full Transcription with timestamps ---\n")
    for segment in transcript_results:
        print(f"[{segment['start_time']}] {segment['text']}\n")

    return transcript_results



@app.route('/yt_notes/transcript', methods=['POST'])
def yt_transcript():
    data = request.json
    url = data.get('url')
    start = data.get('start_time')
    duration = data.get('duration')

    if not all([url, start, duration]):
        return jsonify({"error": "Missing url, start_time, or duration"}), 400

    results = main(url, start, duration)
    return jsonify({"transcript": results})

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=5000)

# if __name__ == "__main__":
#     url = "https://youtu.be/S03cRZ-NO3k?si=uAWqB1DSHAt7sIvT"
#     start = "00:01:00"
#     duration = "00:00:50"
#
#     result = main(url, start, duration)
