from flask import Flask, request, jsonify
from waitress import serve
from yt_trimmer import main_func_transcribe

app = Flask(__name__)

@app.route('/yt_notes/transcript', methods=['POST'])
def yt_transcript():
    data = request.json
    url = data.get('url')
    start = data.get('start_time')
    duration = data.get('duration')

    if not all([url, start, duration]):
        return jsonify({"error": "Missing url, start_time, or duration"}), 400

    result = main_func_transcribe(url, start, duration)
    print(result)
    return jsonify({"transcript": result})

if __name__ == "__main__":
    print("Starting Youtube Notes Transcription")
    serve(app, host="0.0.0.0", port=5000)
