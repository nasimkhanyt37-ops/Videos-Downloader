from flask import Flask, request, render_template, jsonify, send_file
from flask_cors import CORS # <-- এই লাইনটি যুক্ত করা হয়েছে
import os
import requests
from datetime import datetime
import yt_dlp

app = Flask(__name__)
CORS(app) # <-- এই লাইনটি যুক্ত করা হয়েছে (এটি অ্যাপের রিকোয়েস্ট ব্লক হতে দেবে না)

app.config['SECRET_KEY'] = 'your-secret-key-here-change-this'

DOWNLOAD_DIR = os.path.join(os.getcwd(), 'downloads')
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

class UniversalDownloader:
    def detect_platform(self, url):
        url = url.lower()
        if 'youtube.com' in url or 'youtu.be' in url:
            return 'youtube'
        elif 'instagram.com' in url:
            return 'instagram'
        elif 'facebook.com' in url or 'fb.watch' in url:
            return 'facebook'
        elif 'tiktok.com' in url:
            return 'tiktok'
        else:
            return 'unknown'
            
    def get_bypass_headers(self, path):
        return {
            'outtmpl': os.path.join(path, 'Video_%(id)s.%(ext)s'),
            'format': 'best',
            'ignoreerrors': True,
            'nocheckcertificate': True,
            'geo_bypass': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Sec-Fetch-Mode': 'navigate'
            }
        }
    
    def download_content(self, url, custom_path=None):
        path = custom_path or DOWNLOAD_DIR
        platform = self.detect_platform(url)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        download_folder = os.path.join(path, f"{platform}_{timestamp}")
        os.makedirs(download_folder, exist_ok=True)
        
        try:
            ydl_opts = self.get_bypass_headers(download_folder)
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                if info is None:
                    return {'status': 'error', 'message': f'Could not extract {platform} info. Might be blocked by server.'}
                    
                return {'status': 'success', 'message': f'{platform} video downloaded successfully!'}
                
        except Exception as e:
            return {'status': 'error', 'message': f'Error: {str(e)}'}

downloader = UniversalDownloader()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        if not url:
            return jsonify({'status': 'error', 'message': 'URL is required'})
        
        result = downloader.download_content(url)
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Server error: {str(e)}'})

@app.route('/download-latest')
def download_latest():
    try:
        all_files = []
        for root, dirs, files in os.walk(DOWNLOAD_DIR):
            for file in files:
                file_path = os.path.join(root, file)
                all_files.append(file_path)
        
        if not all_files:
            return jsonify({'error': 'No files found'}), 404
            
        latest_file = max(all_files, key=os.path.getmtime)
        filename = os.path.basename(latest_file)
        
        return send_file(latest_file, as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
