from flask import Flask, request, send_file, jsonify
import os
import yt_dlp
import urllib.parse
from googleapiclient.discovery import build
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TCON

# Flask app setup
app = Flask(__name__)

# YouTube API Configuration
API_KEY = "YOUR_YOUTUBE_API_KEY"  # Replace with your actual API Key
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

def search_video(song_name):
    """Search YouTube and return video details."""
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)

    search_response = youtube.search().list(
        q=song_name, part="id,snippet", maxResults=1, type="video"
    ).execute()

    for item in search_response.get("items", []):
        if item["id"]["kind"] == "youtube#video":
            video_id = item["id"]["videoId"]
            title = item["snippet"]["title"]
            channel_name = item["snippet"]["channelTitle"]
            artist = title.split("-")[0].strip() if "-" in title else "Unknown Artist"
            album = f"{channel_name} Collection"
            return video_id, title, artist, album, channel_name

    return None, None, None, None, None

def download_mp3(video_id, filename):
    """Download YouTube video as MP3."""
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
        'outtmpl': filename.replace(".mp3", "") + ".%(ext)s"  # Ensure correct filename format
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f"https://www.youtube.com/watch?v={video_id}"])

    return filename if os.path.exists(filename) else None

def add_metadata(filename, title, artist, album, channel_name):
    """Embed metadata into the MP3 file."""
    if filename and os.path.exists(filename):
        audio = MP3(filename, ID3=ID3)
        audio.tags.add(TIT2(encoding=3, text=title))  # Title
        audio.tags.add(TPE1(encoding=3, text=artist))  # Artist
        audio.tags.add(TALB(encoding=3, text=album))  # Album
        audio.tags.add(TCON(encoding=3, text=f"Downloaded from {channel_name}"))  # Comment
        audio.save()

@app.route('/')
def home():
    return "🎶 YouTube to MP3 Downloader API Running!"

@app.route('/download', methods=['GET'])
def download_song():
    """API Endpoint to download a song"""
    song_name = request.args.get('song')
    
    if not song_name:
        return jsonify({"error": "Please provide a song name using ?song= parameter"}), 400

    video_id, title, artist, album, channel_name = search_video(song_name)
    
    if not video_id:
        return jsonify({"error": "Song not found"}), 404

    mp3_filename = f"{song_name}.mp3"
    downloaded_file = download_mp3(video_id, mp3_filename)

    if not downloaded_file:
        return jsonify({"error": "Failed to download"}), 500

    add_metadata(downloaded_file, title, artist, album, channel_name)

    return send_file(downloaded_file, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
