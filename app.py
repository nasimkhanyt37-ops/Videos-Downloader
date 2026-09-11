from flask import Flask, request, render_template, jsonify, send_file
import os
import tempfile
import threading
import requests
import json
import re
from datetime import datetime
import yt_dlp
import instaloader
from werkzeug.utils import secure_filename
import zipfile
import shutil

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-this'

# Create downloads directory if it doesn't exist
DOWNLOAD_DIR = os.path.join(os.getcwd(), 'downloads')
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

class UniversalDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def detect_platform(self, url):
        url = url.lower()
        if 'youtube.com' in url or 'youtu.be' in url:
            return 'youtube'
        elif 'instagram.com' in url:
            return 'instagram'
        elif 'facebook.com' in url or 'fb.watch' in url:
            return 'facebook'
        elif 'twitter.com' in url or 'x.com' in url:
            return 'twitter'
        elif 'tiktok.com' in url:
            return 'tiktok'
        else:
            return 'unknown'
    
    def download_youtube_content(self, url, path):
        try:
            ydl_opts = {
                'outtmpl': os.path.join(path, '%(uploader)s_%(id)s.%(ext)s'),
                'format': 'best[height<=1080]',
                'ignoreerrors': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if info is None:
                    return {'status': 'error', 'message': 'Could not extract video info.'}
                return {'status': 'success', 'message': 'YouTube content downloaded!'}
        except Exception as e:
            return {'status': 'error', 'message': f'YouTube error: {str(e)}'}
    
    def download_tiktok_content(self, url, path):
        try:
            ydl_opts = {
                'outtmpl': os.path.join(path, 'TikTok_%(id)s.%(ext)s'),
                'format': 'best',
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if info is None:
                    return {'status': 'error', 'message': 'Could not extract TikTok info.'}
                return {'status': 'success', 'message': 'TikTok video downloaded!'}
        except Exception as e:
            return {'status': 'error', 'message': f'TikTok error: {str(e)}'}
    
    def download_facebook_content(self, url, path):
        try:
            ydl_opts = {
                'outtmpl': os.path.join(path, 'Facebook_%(id)s.%(ext)s'),
                'format': 'best',
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if info is None:
                    return {'status': 'error', 'message': 'Could not extract Facebook info.'}
                return {'status': 'success', 'message': 'Facebook content downloaded!'}
        except Exception as e:
            return {'status': 'error', 'message': f'Facebook error: {str(e)}'}
            
    def download_generic_content(self, url, path):
        try:
            ydl_opts = {
                'outtmpl': os.path.join(path, 'Video_%(id)s.%(ext)s'),
                'format': 'best',
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if info is None:
                    return {'status': 'error', 'message': 'Could not extract info.'}
                return {'status': 'success', 'message': 'Content downloaded!'}
        except Exception as e:
            return {'status': 'error', 'message': f'Download error: {str(e)}'}
    
    def download_content(self, url, custom_path=None):
        path = custom_path or DOWNLOAD_DIR
        platform = self.detect_platform(url)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        download_folder = os.path.join(path, f"{platform}_{timestamp}")
        os.makedirs(download_folder, exist_ok=True)
        
        try:
            if platform == 'youtube':
                return self.download_youtube_content(url, download_folder)
            elif platform == 'tiktok':
                return self.download_tiktok_content(url, download_folder)
            elif platform == 'facebook':
                return self.download_facebook_content(url, download_folder)
            else:
                return self.download_generic_content(url, download_folder)
        except Exception as e:
            return {'status': 'error', 'message': f'Unexpected error: {str(e)}'}

downloader = UniversalDownloader()

@app.route('/download', methods=['POST'])
def download():
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        if not url:
            return jsonify({'status': 'error', 'message': 'URL is required'})
        
        platform = downloader.detect_platform(url)
        result = downloader.download_content(url)
        result['platform'] = platform
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Server error: {str(e)}'})

# --- ম্যাজিক ফিক্স: লেটেস্ট ফাইল ডাউনলোডের রাউট ---
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
            
        # সবচেয়ে নতুন ফাইলটি খুঁজে বের করা
        latest_file = max(all_files, key=os.path.getmtime)
        filename = os.path.basename(latest_file)
        
        return send_file(latest_file, as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
