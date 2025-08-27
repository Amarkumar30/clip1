from flask import Blueprint, jsonify, request
import yt_dlp
import os
import tempfile
import google.generativeai as genai
import re
import time
import requests
from urllib.parse import urlparse, parse_qs
import subprocess

video_new_bp = Blueprint('video_new', __name__)

# Initialize Gemini client with your API key
api_key = "AIzaSyC28hIWcYoycpYgMR09c8NFuTDnNRNHO5k"
genai.configure(api_key=api_key)

def extract_video_id(url):
    """Extract YouTube video ID from URL"""
    try:
        parsed_url = urlparse(url)
        if parsed_url.hostname in ['www.youtube.com', 'youtube.com']:
            if parsed_url.path == '/watch':
                return parse_qs(parsed_url.query).get('v', [None])[0]
            elif parsed_url.path.startswith('/embed/'):
                return parsed_url.path.split('/')[2]
        elif parsed_url.hostname in ['youtu.be']:
            return parsed_url.path[1:]
        return None
    except:
        return None

def download_audio_method1(youtube_url):
    """Method 1: Standard yt-dlp download"""
    try:
        temp_dir = tempfile.mkdtemp()
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'ignoreerrors': False,
            'no_check_certificate': True,
            'prefer_ffmpeg': True,
            'geo_bypass': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
        }
        
        print(f"Method 1: Downloading {youtube_url}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            
            # Find the downloaded audio file
            for file in os.listdir(temp_dir):
                if file.endswith('.mp3'):
                    audio_path = os.path.join(temp_dir, file)
                    print(f"Method 1 success: {audio_path}")
                    return audio_path, title, duration
            
            # If no mp3 file found, look for other audio formats
            for file in os.listdir(temp_dir):
                if any(file.endswith(ext) for ext in ['.m4a', '.webm', '.ogg', '.wav']):
                    audio_path = os.path.join(temp_dir, file)
                    print(f"Method 1 success (other format): {audio_path}")
                    return audio_path, title, duration
                    
        return None, None, None
        
    except Exception as e:
        print(f"Method 1 failed: {str(e)}")
        return None, None, None

def download_audio_method2(youtube_url):
    """Method 2: Simple format selection"""
    try:
        temp_dir = tempfile.mkdtemp()
        
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }
        
        print(f"Method 2: Downloading {youtube_url}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            
            # Find any audio file
            for file in os.listdir(temp_dir):
                if any(file.endswith(ext) for ext in ['.mp3', '.m4a', '.webm', '.ogg', '.wav']):
                    audio_path = os.path.join(temp_dir, file)
                    print(f"Method 2 success: {audio_path}")
                    return audio_path, title, duration
                    
        return None, None, None
        
    except Exception as e:
        print(f"Method 2 failed: {str(e)}")
        return None, None, None

def download_audio_method3(youtube_url):
    """Method 3: Direct download without conversion"""
    try:
        temp_dir = tempfile.mkdtemp()
        
        ydl_opts = {
            'format': 'worstaudio/worst',  # Sometimes smaller files work better
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'extract_audio': True,
            'audio_format': 'mp3',
        }
        
        print(f"Method 3: Downloading {youtube_url}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            
            # Find any audio file
            for file in os.listdir(temp_dir):
                if any(file.endswith(ext) for ext in ['.mp3', '.m4a', '.webm', '.ogg', '.wav']):
                    audio_path = os.path.join(temp_dir, file)
                    print(f"Method 3 success: {audio_path}")
                    return audio_path, title, duration
                    
        return None, None, None
        
    except Exception as e:
        print(f"Method 3 failed: {str(e)}")
        return None, None, None

def download_audio(youtube_url):
    """Try multiple download methods"""
    methods = [download_audio_method1, download_audio_method2, download_audio_method3]
    
    for i, method in enumerate(methods, 1):
        print(f"Trying download method {i}...")
        result = method(youtube_url)
        if result[0]:  # If audio_path is not None
            return result
        time.sleep(1)  # Brief pause between attempts
    
    print("All download methods failed")
    return None, None, None

def transcribe_audio(audio_path):
    """Transcribe audio using Gemini 1.5 Flash"""
    try:
        print(f"Transcribing audio file: {audio_path}")
        
        # Check if file exists and is readable
        if not os.path.exists(audio_path):
            print("Audio file does not exist")
            return None
            
        file_size = os.path.getsize(audio_path)
        print(f"Audio file size: {file_size} bytes")
        
        if file_size == 0:
            print("Audio file is empty")
            return None
        
        # Use the file directly
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Read the audio file as bytes
        with open(audio_path, 'rb') as audio_file:
            audio_data = audio_file.read()
        
        prompt = "Please transcribe this audio file completely and accurately. Provide the full transcript as a single block of text. Include all spoken content with proper punctuation and formatting."
        
        print("Sending to Gemini for transcription...")
        response = model.generate_content([
            prompt,
            {"mime_type": "audio/mpeg", "data": audio_data}
        ])
        
        print("Transcription successful")
        return response.text
        
    except Exception as e:
        print(f"Error transcribing audio with Gemini: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def generate_twitter_thread(transcript_text, video_title, youtube_url):
    """Generate Twitter thread from transcript"""
    try:
        # Limit transcript length to avoid token limits
        truncated_transcript = transcript_text[:5000] if transcript_text else ""
        
        prompt = f"""
        Act as a social media copywriter. Based on the following video transcript, create a Twitter thread that summarizes the key takeaways, arguments, and interesting points.

        Video Title: {video_title}
        Transcript: {truncated_transcript}

        Requirements:
        1. Create a coherent Twitter thread with 4-6 numbered tweets (Tweet 1:, Tweet 2:, etc.)
        2. Each tweet must be under 280 characters
        3. Focus on the most valuable insights and key points
        4. Make it engaging and shareable
        5. The final tweet should include a CTA: "Watch the full video here: {youtube_url}"
        6. Format as: 
        Tweet 1: [content]
        Tweet 2: [content]
        etc.

        Generate the Twitter thread:
        """
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                max_output_tokens=2000,
                temperature=0.7
            )
        )
        return response.text
    except Exception as e:
        print(f"Error generating Twitter thread: {str(e)}")
        import traceback
        traceback.print_exc()
        return "Failed to generate Twitter thread. Please try again."

def generate_reel_suggestions(transcript_text, video_title):
    """Generate reel clip suggestions"""
    try:
        # Limit transcript length to avoid token limits
        truncated_transcript = transcript_text[:4000] if transcript_text else ""
        
        prompt = f"""
        Act as a video editor and content strategist. Based on the following video transcript, identify 3-5 distinct, impactful moments that would work well as short-form clips for Instagram Reels or TikTok.

        Video Title: {video_title}
        Transcript: {truncated_transcript}

        For each suggestion, provide:
        1. A short, engaging title for the clip
        2. A punchy caption for social media (under 150 characters)
        3. Brief explanation of why this moment works as a clip

        Format your response as:
        Clip 1:
        Title: [title]
        Caption: [caption]
        Why it works: [explanation]

        Clip 2:
        Title: [title]
        Caption: [caption]
        Why it works: [explanation]

        Generate 3-5 reel suggestions:
        """
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                max_output_tokens=2000,
                temperature=0.7
            )
        )
        return response.text
    except Exception as e:
        print(f"Error generating reel suggestions: {str(e)}")
        import traceback
        traceback.print_exc()
        return "Failed to generate reel suggestions. Please try again."

@video_new_bp.route('/process', methods=['POST'])
def process_video():
    """Main endpoint to process YouTube video"""
    try:
        data = request.json
        youtube_url = data.get('url') or data.get('youtube_url')
        email = data.get('email', '')
        
        if not youtube_url:
            return jsonify({'error': 'YouTube URL is required'}), 400
        
        video_id = extract_video_id(youtube_url)
        if not video_id:
            return jsonify({'error': 'Invalid YouTube URL. Please provide a valid YouTube URL.'}), 400
        
        print(f"Processing YouTube video: {youtube_url}")
        print(f"Video ID: {video_id}")
        
        # Download audio
        print("Step 1: Downloading audio...")
        audio_path, title, duration = download_audio(youtube_url)
        if not audio_path:
            return jsonify({'error': 'Failed to download audio from video. Please try a different video or check if YouTube is accessible from your network.'}), 500
        
        print(f"Audio downloaded: {title}")
        
        # Transcribe audio
        print("Step 2: Transcribing audio...")
        transcript_text = transcribe_audio(audio_path)
        if not transcript_text:
            # Clean up audio file
            try:
                if audio_path and os.path.exists(audio_path):
                    os.remove(audio_path)
                    os.rmdir(os.path.dirname(audio_path))
            except:
                pass
            return jsonify({'error': 'Failed to transcribe audio. The audio might be too short or contain no speech.'}), 500
        
        print("Audio transcribed successfully")
        print(f"Transcript length: {len(transcript_text)} characters")
        
        # Clean up audio file
        try:
            if audio_path and os.path.exists(audio_path):
                os.remove(audio_path)
                os.rmdir(os.path.dirname(audio_path))
                print("Temporary files cleaned up")
        except Exception as e:
            print(f"Warning: Could not clean up temp files: {e}")
        
        # Generate content
        print("Step 3: Generating Twitter thread...")
        twitter_thread = generate_twitter_thread(transcript_text, title, youtube_url)
        
        print("Step 4: Generating reel suggestions...")
        reel_suggestions = generate_reel_suggestions(transcript_text, title)
        
        # Format duration
        if duration:
            minutes = duration // 60
            seconds = duration % 60
            duration_formatted = f"{minutes}:{seconds:02d}"
        else:
            duration_formatted = "Unknown"
        
        print("Processing complete!")
        
        return jsonify({
            'success': True,
            'video_title': title,
            'duration': duration_formatted,
            'twitter_thread': twitter_thread,
            'reel_suggestions': reel_suggestions,
            'email': email
        })
        
    except Exception as e:
        print(f"Processing failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

@video_new_bp.route('/validate', methods=['POST'])
def validate_url():
    """Validate YouTube URL"""
    try:
        data = request.json
        youtube_url = data.get('url') or data.get('youtube_url')
        
        if not youtube_url:
            return jsonify({'valid': False, 'error': 'URL is required'})
        
        video_id = extract_video_id(youtube_url)
        if not video_id:
            return jsonify({'valid': False, 'error': 'Invalid YouTube URL. Please provide a valid YouTube URL.'})
        
        return jsonify({'valid': True, 'video_id': video_id})
        
    except Exception as e:
        return jsonify({'valid': False, 'error': str(e)})

@video_new_bp.route('/demo', methods=['POST'])
def demo_process():
    """Demo endpoint that returns sample data without actual processing"""
    try:
        data = request.json
        youtube_url = data.get('url', 'https://www.youtube.com/watch?v=dQw4w9WgXcQ')
        
        demo_data = {
            'success': True,
            'video_title': 'Demo: The Power of Authentic Content Creation',
            'duration': '15:00',
            'twitter_thread': f"""Tweet 1: 🧵 Just discovered an amazing insight from this video! Here's what caught my attention and why it matters for content creators everywhere.

Tweet 2: The key takeaway? Authenticity beats perfection every single time. When you show up as your real self, your audience connects on a deeper level.

Tweet 3: Three practical tips mentioned:
• Be vulnerable in your storytelling
• Share behind-the-scenes moments
• Don't be afraid to show your failures

Tweet 4: The most powerful quote: "Your mess becomes your message, and your test becomes your testimony." This resonates so deeply with building genuine connections.

Tweet 5: If you're a content creator struggling with imposter syndrome, this video is a must-watch. It's a reminder that your unique perspective is exactly what the world needs.

Tweet 6: Watch the full video here: {youtube_url}""",
            
            'reel_suggestions': """Clip 1:
Title: "The Authenticity Secret"
Caption: POV: You realize authenticity beats perfection every time ✨ Your real self is your superpower! #ContentCreator #Authenticity
Why it works: This moment captures a powerful mindset shift that resonates with creators

Clip 2:
Title: "Behind the Scenes Magic"
Caption: The magic happens when you show what's behind the curtain 🎭 Stop hiding your process! #BehindTheScenes #CreatorTips
Why it works: Visual storytelling opportunity with relatable creator struggles

Clip 3:
Title: "Failure is Fuel"
Caption: Your biggest failures become your best content 💪 Don't hide them, share them! #FailureToSuccess #GrowthMindset
Why it works: Inspirational message with strong emotional hook

Clip 4:
Title: "Your Mess = Your Message"
Caption: "Your mess becomes your message" - this hit different 🎯 What's your story? #Storytelling #PersonalBrand
Why it works: Quotable moment perfect for engagement and shares""",
            'email': data.get('email', 'demo@clipzaar.com')
        }
        
        return jsonify(demo_data)
        
    except Exception as e:
        return jsonify({'error': f'Demo processing failed: {str(e)}'}), 500
    
    # Add this to your video_processor_new.py
@video_new_bp.route('/test-download', methods=['POST'])
def test_download():
    """Test endpoint to debug download issues"""
    try:
        data = request.json
        youtube_url = data.get('url')
        
        if not youtube_url:
            return jsonify({'error': 'URL required'}), 400
        
        video_id = extract_video_id(youtube_url)
        if not video_id:
            return jsonify({'error': 'Invalid YouTube URL'}), 400
        
        print(f"Testing download for: {youtube_url}")
        print(f"Video ID: {video_id}")
        
        # Test each method
        methods = [download_audio_method1, download_audio_method2, download_audio_method3]
        results = []
        
        for i, method in enumerate(methods, 1):
            print(f"\n--- Testing Method {i} ---")
            try:
                audio_path, title, duration = method(youtube_url)
                results.append({
                    'method': i,
                    'success': audio_path is not None,
                    'audio_path': audio_path,
                    'title': title,
                    'duration': duration
                })
                if audio_path:
                    print(f"Method {i} SUCCESS: {audio_path}")
                else:
                    print(f"Method {i} FAILED")
            except Exception as e:
                print(f"Method {i} ERROR: {str(e)}")
                results.append({
                    'method': i,
                    'success': False,
                    'error': str(e)
                })
            
            # Clean up
            try:
                if audio_path and os.path.exists(audio_path):
                    os.remove(audio_path)
                    dir_path = os.path.dirname(audio_path)
                    if os.path.exists(dir_path):
                        os.rmdir(dir_path)
            except:
                pass
        
        return jsonify({
            'url': youtube_url,
            'video_id': video_id,
            'results': results
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500