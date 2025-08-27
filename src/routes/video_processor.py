from flask import Blueprint, jsonify, request
import yt_dlp
import os
import tempfile
import openai
import re
from urllib.parse import urlparse, parse_qs

video_bp = Blueprint('video', __name__)

# Initialize OpenAI client
client = openai.OpenAI()

def extract_video_id(url):
    """Extract YouTube video ID from URL"""
    parsed_url = urlparse(url)
    if parsed_url.hostname in ['www.youtube.com', 'youtube.com']:
        if parsed_url.path == '/watch':
            return parse_qs(parsed_url.query).get('v', [None])[0]
    elif parsed_url.hostname in ['youtu.be']:
        return parsed_url.path[1:]
    return None

def download_audio(youtube_url):
    """Download audio from YouTube video"""
    try:
        # Create temporary directory for audio files
        temp_dir = tempfile.mkdtemp()
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            
            # Find the downloaded audio file
            for file in os.listdir(temp_dir):
                if file.endswith('.mp3'):
                    audio_path = os.path.join(temp_dir, file)
                    return audio_path, title, duration
                    
        return None, None, None
    except Exception as e:
        print(f"Error downloading audio: {str(e)}")
        return None, None, None

def transcribe_audio(audio_path):
    """Transcribe audio using OpenAI Whisper"""
    try:
        with open(audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["segment"]
            )
        return transcript
    except Exception as e:
        print(f"Error transcribing audio: {str(e)}")
        return None

def generate_twitter_thread(transcript_text, video_title, youtube_url):
    """Generate Twitter thread from transcript"""
    prompt = f"""
    Act as a social media copywriter. Based on the following video transcript, create a Twitter thread that summarizes the key takeaways, arguments, and interesting points.

    Video Title: {video_title}
    Transcript: {transcript_text}

    Requirements:
    1. Create a coherent Twitter thread with numbered tweets
    2. Each tweet must be under 280 characters
    3. Focus on the most valuable insights and key points
    4. Make it engaging and shareable
    5. The final tweet should include a CTA: "Watch the full video here: {youtube_url}"
    6. Format as: Tweet 1: [content], Tweet 2: [content], etc.

    Generate the Twitter thread:
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating Twitter thread: {str(e)}")
        return None

def generate_reel_suggestions(transcript_segments, video_title):
    """Generate reel clip suggestions with timestamps"""
    # Convert segments to text with timestamps
    segments_text = ""
    for segment in transcript_segments:
        start_time = segment.get('start', 0)
        end_time = segment.get('end', 0)
        text = segment.get('text', '')
        segments_text += f"[{start_time:.1f}s - {end_time:.1f}s]: {text}\n"
    
    prompt = f"""
    Act as a video editor and content strategist. Based on the following timestamped video transcript, identify 3-5 distinct, impactful moments that would work well as short-form clips for Instagram Reels or TikTok.

    Video Title: {video_title}
    Timestamped Transcript:
    {segments_text}

    For each suggestion, provide:
    1. Start timestamp and end timestamp (format: MM:SS - MM:SS)
    2. A short, engaging title for the clip
    3. A punchy caption for social media (under 150 characters)
    4. Brief explanation of why this moment works as a clip

    Format your response as:
    Clip 1:
    Timestamp: [start] - [end]
    Title: [title]
    Caption: [caption]
    Why it works: [explanation]

    Generate 3-5 reel suggestions:
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating reel suggestions: {str(e)}")
        return None

@video_bp.route('/process', methods=['POST'])
def process_video():
    """Main endpoint to process YouTube video"""
    try:
        data = request.json
        youtube_url = data.get('youtube_url')
        email = data.get('email', '')
        
        if not youtube_url:
            return jsonify({'error': 'YouTube URL is required'}), 400
        
        # Validate YouTube URL
        video_id = extract_video_id(youtube_url)
        if not video_id:
            return jsonify({'error': 'Invalid YouTube URL'}), 400
        
        # Step 1: Download audio
        audio_path, title, duration = download_audio(youtube_url)
        if not audio_path:
            return jsonify({'error': 'Failed to download audio from video'}), 500
        
        # Step 2: Transcribe audio
        transcript = transcribe_audio(audio_path)
        if not transcript:
            return jsonify({'error': 'Failed to transcribe audio'}), 500
        
        # Clean up audio file
        try:
            os.remove(audio_path)
            os.rmdir(os.path.dirname(audio_path))
        except:
            pass
        
        # Step 3: Generate Twitter thread
        twitter_thread = generate_twitter_thread(transcript.text, title, youtube_url)
        
        # Step 4: Generate reel suggestions
        reel_suggestions = generate_reel_suggestions(transcript.segments, title)
        
        # Return results
        return jsonify({
            'success': True,
            'video_title': title,
            'duration': duration,
            'twitter_thread': twitter_thread,
            'reel_suggestions': reel_suggestions,
            'email': email
        })
        
    except Exception as e:
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

@video_bp.route('/validate', methods=['POST'])
def validate_url():
    """Validate YouTube URL"""
    try:
        data = request.json
        youtube_url = data.get('youtube_url')
        
        if not youtube_url:
            return jsonify({'valid': False, 'error': 'URL is required'})
        
        video_id = extract_video_id(youtube_url)
        if not video_id:
            return jsonify({'valid': False, 'error': 'Invalid YouTube URL'})
        
        return jsonify({'valid': True, 'video_id': video_id})
        
    except Exception as e:
        return jsonify({'valid': False, 'error': str(e)})

