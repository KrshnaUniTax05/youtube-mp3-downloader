from flask import Flask, request, send_file
import os
import yt_dlp
import urllib.parse
from googleapiclient.discovery import build
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TCON

# Flask App
app = Flask(__name__)

# YouTube API Configuration
API_KEY = "YOUR_YOUTUBE_API_KEY"  # Replace with your API Key
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
        'outtmpl': filename.replace(".mp3", "") + ".%(ext)s"
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f"https://www.youtube.com/watch?v={video_id}"])

    return filename if os.path.exists(filename) else filename.replace(".mp3", ".mp3.mp3")

@app.route("/")
def home():
    return "🎵 Welcome! Use /download?song=SONG_NAME to get your MP3."

@app.route("/download")
def download_song():
    song_name = request.args.get("song", "")
    if not song_name:
        return "❌ Error: No song provided. Use /download?song=SONG_NAME", 400

    video_id, title, artist, album, channel_name = search_video(song_name)
    if not video_id:
        return "❌ Error: No video found.", 404

    filename = f"{song_name}.mp3"
    downloaded_file = download_mp3(video_id, filename)

    if downloaded_file:
        return send_file(downloaded_file, as_attachment=True)
    else:
        return "❌ Error: Download failed.", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
