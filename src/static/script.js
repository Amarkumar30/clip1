// DOM Elements
const videoInput = document.getElementById('video-url');
const getClipsBtn = document.getElementById('get-clips-btn');
const processingModal = document.getElementById('processing-modal');
const resultsModal = document.getElementById('results-modal');
const closeResultsBtn = document.getElementById('close-results');
const processingStatus = document.getElementById('processing-status');
const videoTitle = document.getElementById('video-title');
const videoDuration = document.getElementById('video-duration');
const twitterContent = document.getElementById('twitter-content');
const reelContent = document.getElementById('reel-content');

// Additional elements for new design
const ctaGetClipsBtn = document.querySelector('.cta-get-clips-btn');
const ctaVideoInput = document.querySelector('.cta-video-input');
const uploadBtn = document.querySelector('.upload-btn');
const previewGetClipsBtn = document.querySelector('.preview-get-clips');
const copyBtns = document.querySelectorAll('.copy-btn');

// Mobile menu toggle
const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
const navMenu = document.querySelector('.nav-menu');
const navAuth = document.querySelector('.nav-auth');

// Utility Functions
function isValidYouTubeURL(url) {
    const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+/;
    return youtubeRegex.test(url);
}

function showModal(modal) {
    modal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
}

function hideModal(modal) {
    modal.classList.add('hidden');
    document.body.style.overflow = 'auto';
}

function updateProcessingStep(stepNumber) {
    // Remove active class from all steps
    document.querySelectorAll('.step').forEach(step => {
        step.classList.remove('active');
    });
    
    // Add active class to current step
    const currentStep = document.getElementById(`step-${stepNumber}`);
    if (currentStep) {
        currentStep.classList.add('active');
    }
}

function updateProcessingStatus(message) {
    if (processingStatus) {
        processingStatus.textContent = message;
    }
}

// Copy to clipboard functionality
function copyToClipboard(text, button) {
    navigator.clipboard.writeText(text).then(() => {
        const originalText = button.textContent;
        button.textContent = 'Copied!';
        button.classList.add('copied');
        
        setTimeout(() => {
            button.textContent = originalText;
            button.classList.remove('copied');
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy text: ', err);
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        
        const originalText = button.textContent;
        button.textContent = 'Copied!';
        button.classList.add('copied');
        
        setTimeout(() => {
            button.textContent = originalText;
            button.classList.remove('copied');
        }, 2000);
    });
}

// Process video function
// In the processVideo function, update the error handling:
async function processVideo(url) {
    if (!isValidYouTubeURL(url)) {
        alert('Please enter a valid YouTube URL (youtube.com or youtu.be)');
        return;
    }

    // Show processing modal
    showModal(processingModal);
    
    try {
        updateProcessingStep(1);
        updateProcessingStatus('Extracting audio from YouTube...');
        
        // Make API call to backend
        const response = await fetch('/api/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url: url,
                email: 'user@clipzaar.com'
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to process video');
        }
        
        // Hide processing modal
        hideModal(processingModal);
        
        // Show results
        displayResults(data);
        
    } catch (error) {
        console.error('Error processing video:', error);
        hideModal(processingModal);
        alert('Error: ' + error.message);
    }
}

// Display results in modal
function displayResults(data) {
    if (videoTitle) videoTitle.textContent = data.video_title;
    if (videoDuration) videoDuration.textContent = `Duration: ${data.duration}`;
    if (twitterContent) twitterContent.textContent = data.twitter_thread;
    if (reelContent) reelContent.textContent = data.reel_suggestions;
    
    showModal(resultsModal);
}

// Event Listeners
if (getClipsBtn) {
    getClipsBtn.addEventListener('click', () => {
        const url = videoInput.value.trim();
        if (url) {
            processVideo(url);
        } else {
            alert('Please enter a YouTube URL');
        }
    });
}

if (ctaGetClipsBtn) {
    ctaGetClipsBtn.addEventListener('click', () => {
        const url = ctaVideoInput.value.trim();
        if (url) {
            processVideo(url);
        } else {
            alert('Please enter a YouTube URL');
        }
    });
}

if (previewGetClipsBtn) {
    previewGetClipsBtn.addEventListener('click', () => {
        // Use a demo URL for the preview
        processVideo('https://www.youtube.com/watch?v=dQw4w9WgXcQ');
    });
}

if (uploadBtn) {
    uploadBtn.addEventListener('click', () => {
        alert('File upload functionality coming soon! For now, please use a YouTube URL.');
    });
}

if (closeResultsBtn) {
    closeResultsBtn.addEventListener('click', () => {
        hideModal(resultsModal);
    });
}

// Copy button functionality
copyBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const targetId = btn.getAttribute('data-target');
        const targetElement = document.getElementById(targetId);
        if (targetElement) {
            copyToClipboard(targetElement.textContent, btn);
        }
    });
});

// Mobile menu toggle
if (mobileMenuToggle && navMenu && navAuth) {
    mobileMenuToggle.addEventListener('click', () => {
        const isVisible = navMenu.style.display === 'flex';
        navMenu.style.display = isVisible ? 'none' : 'flex';
        navAuth.style.display = isVisible ? 'none' : 'flex';
    });
}

// Enter key support for inputs
if (videoInput) {
    videoInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            getClipsBtn.click();
        }
    });
}

if (ctaVideoInput) {
    ctaVideoInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            ctaGetClipsBtn.click();
        }
    });
}

// Close modals when clicking outside
[processingModal, resultsModal].forEach(modal => {
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                hideModal(modal);
            }
        });
    }
});

// Smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Add scroll effect to navbar
window.addEventListener('scroll', () => {
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        if (window.scrollY > 50) {
            navbar.style.background = 'rgba(10, 10, 10, 0.98)';
        } else {
            navbar.style.background = 'rgba(10, 10, 10, 0.95)';
        }
    }
});

// Initialize page
document.addEventListener('DOMContentLoaded', () => {
    console.log('Clipzaar initialized successfully!');
    
    // Auto-focus on the main input
    if (videoInput) {
        videoInput.focus();
    }
});