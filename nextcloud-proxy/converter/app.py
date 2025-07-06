import os
import subprocess
import uuid
import re
from flask import Flask, request, send_file, after_this_request

app = Flask(__name__)
UPLOAD_FOLDER = '/app/tmp'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def sanitize_filename(name):
    """Remove invalid characters from filename"""
    return re.sub(r'[^\w\-_\. ]', '', name).strip()

@app.route('/convert', methods=['POST'])
def convert():
    url = request.form['url']
    if 'youtube.com/' not in url and 'youtu.be/' not in url:
        return "Invalid URL", 400
    
    try:
        # Get video title
        title_result = subprocess.run([
            'yt-dlp',
            '--print', 'title',
            '--no-simulate',
            url
        ], capture_output=True, text=True, timeout=30)
        
        if title_result.returncode != 0:
            return f"Failed to get video title: {title_result.stderr}", 500
        
        raw_title = title_result.stdout.strip()
        clean_title = sanitize_filename(raw_title)
        filename = f"{clean_title}.mp3"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
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
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception as e:
                app.logger.error(f"Error removing file {filepath}: {e}")
            return response
        
        return send_file(filepath, as_attachment=True, download_name=filename)
    
    except Exception as e:
        return f"Conversion failed: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
