from flask import Blueprint, jsonify, request
import re
from urllib.parse import urlparse, parse_qs
import time

video_bp = Blueprint('video', __name__)

def extract_video_id(url):
    """Extract YouTube video ID from URL"""
    parsed_url = urlparse(url)
    if parsed_url.hostname in ['www.youtube.com', 'youtube.com']:
        if parsed_url.path == '/watch':
            return parse_qs(parsed_url.query).get('v', [None])[0]
    elif parsed_url.hostname in ['youtu.be']:
        return parsed_url.path[1:]
    return None

@video_bp.route('/process', methods=['POST'])
def process_video():
    """Demo endpoint - returns sample content for demonstration"""
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
        
        # Simulate processing time
        time.sleep(3)
        
        # Demo Twitter thread
        twitter_thread = """Tweet 1: 🧵 Just discovered an amazing insight from this video! Here's what caught my attention and why it matters for content creators everywhere.

Tweet 2: The key takeaway? Authenticity beats perfection every single time. When you show up as your real self, your audience connects on a deeper level.

Tweet 3: Three practical tips mentioned:
• Be vulnerable in your storytelling
• Share behind-the-scenes moments
• Don't be afraid to show your failures

Tweet 4: The most powerful quote: "Your mess becomes your message, and your test becomes your testimony." This resonates so deeply with building genuine connections.

Tweet 5: If you're a content creator struggling with imposter syndrome, this video is a must-watch. It's a reminder that your unique perspective is exactly what the world needs.

Tweet 6: Watch the full video here: """ + youtube_url
        
        # Demo reel suggestions
        reel_suggestions = """Clip 1:
Timestamp: 02:15 - 02:45
Title: "The Authenticity Secret"
Caption: POV: You realize authenticity beats perfection every time ✨ Your real self is your superpower! #ContentCreator #Authenticity
Why it works: This moment captures a powerful mindset shift that resonates with creators

Clip 2:
Timestamp: 05:30 - 06:00
Title: "Behind the Scenes Magic"
Caption: The magic happens when you show what's behind the curtain 🎭 Stop hiding your process! #BehindTheScenes #CreatorTips
Why it works: Visual storytelling opportunity with relatable creator struggles

Clip 3:
Timestamp: 08:45 - 09:15
Title: "Failure is Fuel"
Caption: Your biggest failures become your best content 💪 Don't hide them, share them! #FailureToSuccess #GrowthMindset
Why it works: Inspirational message with strong emotional hook

Clip 4:
Timestamp: 12:20 - 12:50
Title: "Your Mess = Your Message"
Caption: "Your mess becomes your message" - this hit different 🎯 What's your story? #Storytelling #PersonalBrand
Why it works: Quotable moment perfect for engagement and shares"""
        
        # Return demo results
        return jsonify({
            'success': True,
            'video_title': 'Demo: The Power of Authentic Content Creation',
            'duration': 900,  # 15 minutes
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

