import os
import subprocess
import uuid
from flask import Flask, request, send_file, after_this_request

app = Flask(__name__)
UPLOAD_FOLDER = '/app/tmp'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/convert', methods=['POST'])
def convert():
    url = request.form['url']
    if 'youtube.com/' not in url and 'youtu.be/' not in url:
        return "Invalid URL", 400
    
    filename = f"{uuid.uuid4()}.mp3"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    
    try:
        # Download and convert to MP3
        subprocess.run([
            'yt-dlp',
            '-x', 
            '--audio-format', 'mp3',
            '--output', filepath,
            url
        ], check=True, timeout=600)
        
        # Cleanup after sending file
        @after_this_request
        def remove_file(response):
            try:
                os.remove(filepath)
            except Exception as e:
                app.logger.error(f"Error removing file {filepath}: {e}")
            return response
        
        return send_file(filepath, as_attachment=True, download_name='converted.mp3')
    
    except Exception as e:
        return f"Conversion failed: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
