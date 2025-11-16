"""
React Interview API - Backend Flask Server
Handles interview flow, question generation, answer evaluation, and scoring
"""

import os
import sys
import logging
import tempfile
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from gemini_client import GeminiClient
from speech_processor import SpeechProcessor

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global interview state
interview_state = {
    'is_active': False,
    'current_question_index': 0,
    'questions': [],
    'answers': [],
    'scores': [],
    'total_score': 0
}

# Initialize components
gemini_client = None
speech_processor = None

def get_gemini_client():
    """Get or create Gemini client instance."""
    global gemini_client
    if gemini_client is None:
        gemini_client = GeminiClient(format_responses=False, use_rules=False)
        logger.info("Gemini client initialized")
    return gemini_client

def get_speech_processor():
    """Get or create speech processor instance."""
    global speech_processor
    if speech_processor is None:
        speech_processor = SpeechProcessor(model_size="base", device="cpu")
        logger.info("Speech processor initialized")
    return speech_processor

def generate_react_questions():
    """Generate 2 React interview questions using Gemini."""
    client = get_gemini_client()
    
    prompt = """You are an experienced React interviewer. Generate exactly 2 React.js interview questions for a mid-level developer.

Requirements:
1. First question: React fundamentals (hooks, state, props, or component lifecycle)
2. Second question: React performance optimization or best practices

Important:
- Each question should be clear and conversational
- Questions should be suitable for a voice interview
- Make questions engaging and practical
- Keep questions under 50 words each

Respond ONLY with a JSON array in this exact format:
["First question here?", "Second question here?"]

Do not include any other text, explanations, or markdown formatting.
"""
    
    try:
        response = client.send_message(prompt)
        # Try to extract JSON array from response
        import json
        
        # Clean up response to extract JSON
        response = response.strip()
        if '```json' in response:
            response = response.split('```json')[1].split('```')[0].strip()
        elif '```' in response:
            response = response.split('```')[1].split('```')[0].strip()
        
        questions = json.loads(response)
        
        if isinstance(questions, list) and len(questions) >= 2:
            logger.info(f"Generated questions successfully: {questions[:2]}")
            return questions[:2]
        else:
            logger.warning("Invalid question format, using fallback")
            # Fallback questions
            return [
                "Can you explain what React hooks are and describe how the useState hook works with a practical example?",
                "What are some key techniques you would use to optimize the performance of a large React application?"
            ]
    except Exception as e:
        logger.error(f"Error generating questions: {e}")
        # Fallback questions with guaranteed quality
        return [
            "Can you explain what React hooks are and describe how the useState hook works with a practical example?",
            "What are some key techniques you would use to optimize the performance of a large React application?"
        ]

def evaluate_answer(question, answer):
    """Evaluate answer using Gemini and return score (0 or 1)."""
    client = get_gemini_client()
    
    prompt = f"""You are an interviewer evaluating a React developer's answer.

Question: {question}

Candidate's Answer: {answer}

Evaluate this answer and determine if it demonstrates sufficient understanding.
Consider:
- Technical accuracy
- Relevance to the question
- Depth of understanding
- Practical knowledge

Respond with ONLY "CORRECT" if the answer is acceptable (award 1 point), or "INCORRECT" if not (award 0 points).
Be reasonably lenient - if the answer shows basic understanding, mark it as CORRECT.
"""
    
    try:
        response = client.send_message(prompt).strip().upper()
        logger.info(f"Evaluation response: {response}")
        
        if "CORRECT" in response and "INCORRECT" not in response:
            return 1
        else:
            return 0
    except Exception as e:
        logger.error(f"Error evaluating answer: {e}")
        return 0

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'React Interview API'
    })

@app.route('/interview/start', methods=['POST'])
def start_interview():
    """Start a new interview session."""
    global interview_state
    
    try:
        # Generate questions
        logger.info("Generating interview questions...")
        questions = generate_react_questions()
        logger.info(f"Questions generated: {questions}")
        
        # Reset interview state
        interview_state = {
            'is_active': True,
            'current_question_index': 0,
            'questions': questions,
            'answers': [],
            'scores': [],
            'total_score': 0
        }
        
        # Get welcome message
        welcome_message = """Welcome to your React.js interview! I'm excited to learn about your React experience and knowledge. 
        
Let me start by introducing myself. I'm your AI interviewer today, and I'll be asking you 2 questions about React. Take your time with each answer, and feel free to provide examples from your experience. Let's begin!"""
        
        first_question = questions[0] if questions else None
        logger.info(f"Starting interview with first question: {first_question}")
        
        return jsonify({
            'status': 'success',
            'message': 'Interview started',
            'welcome_message': welcome_message,
            'total_questions': len(questions),
            'first_question': first_question
        })
        
    except Exception as e:
        logger.error(f"Error starting interview: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/interview/question', methods=['GET'])
def get_current_question():
    """Get the current question."""
    if not interview_state['is_active']:
        return jsonify({'status': 'error', 'error': 'No active interview'}), 400
    
    index = interview_state['current_question_index']
    
    if index >= len(interview_state['questions']):
        return jsonify({
            'status': 'success',
            'completed': True,
            'message': 'All questions completed'
        })
    
    return jsonify({
        'status': 'success',
        'question': interview_state['questions'][index],
        'question_number': index + 1,
        'total_questions': len(interview_state['questions'])
    })

@app.route('/interview/transcribe', methods=['POST'])
def transcribe_audio():
    """Transcribe audio from the user."""
    try:
        if 'audio' not in request.files:
            return jsonify({'status': 'error', 'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'status': 'error', 'error': 'No audio file selected'}), 400
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
            audio_file.save(temp_file.name)
            temp_file_path = temp_file.name
        
        try:
            processor = get_speech_processor()
            transcription = processor.transcribe_audio_file(temp_file_path)
            
            if not transcription:
                transcription = "I couldn't hear your response clearly. Please try again."
            
            return jsonify({
                'status': 'success',
                'transcription': transcription
            })
            
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
        
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/interview/submit', methods=['POST'])
def submit_answer():
    """Submit an answer for the current question."""
    global interview_state
    
    if not interview_state['is_active']:
        return jsonify({'status': 'error', 'error': 'No active interview'}), 400
    
    try:
        data = request.get_json()
        if not data or 'answer' not in data:
            return jsonify({'status': 'error', 'error': 'Answer is required'}), 400
        
        answer = data['answer'].strip()
        index = interview_state['current_question_index']
        
        if index >= len(interview_state['questions']):
            return jsonify({'status': 'error', 'error': 'No more questions'}), 400
        
        question = interview_state['questions'][index]
        
        # Evaluate the answer
        score = evaluate_answer(question, answer)
        
        # Store answer and score
        interview_state['answers'].append(answer)
        interview_state['scores'].append(score)
        interview_state['total_score'] += score
        
        # Move to next question
        interview_state['current_question_index'] += 1
        
        # Check if interview is complete
        is_complete = interview_state['current_question_index'] >= len(interview_state['questions'])
        
        next_question = None
        if not is_complete:
            next_question = interview_state['questions'][interview_state['current_question_index']]
            logger.info(f"Moving to next question {interview_state['current_question_index'] + 1}: {next_question}")
        else:
            logger.info("All questions completed")
        
        return jsonify({
            'status': 'success',
            'score': score,
            'is_complete': is_complete,
            'next_question': next_question,
            'question_number': interview_state['current_question_index'] + 1 if not is_complete else None,
            'total_questions': len(interview_state['questions'])
        })
        
    except Exception as e:
        logger.error(f"Error submitting answer: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/interview/complete', methods=['POST'])
def complete_interview():
    """Complete the interview and get final score."""
    global interview_state
    
    if not interview_state['is_active']:
        return jsonify({'status': 'error', 'error': 'No active interview'}), 400
    
    try:
        # Generate closing message
        client = get_gemini_client()
        
        score = interview_state['total_score']
        total = len(interview_state['questions'])
        
        closing_message = f"""Thank you for participating in this React interview! 
        
You've completed all {total} questions. Your final score is {score} out of {total}.

{'Excellent work! You demonstrated strong knowledge of React concepts.' if score == total else 
 'Good effort! Keep practicing and deepening your React knowledge.' if score > 0 else
 'Thank you for your time. I recommend reviewing React fundamentals and practicing more.'}

Best of luck with your React development journey!"""
        
        # Mark interview as inactive
        interview_state['is_active'] = False
        
        return jsonify({
            'status': 'success',
            'closing_message': closing_message,
            'final_score': score,
            'total_questions': total,
            'questions': interview_state['questions'],
            'answers': interview_state['answers'],
            'scores': interview_state['scores']
        })
        
    except Exception as e:
        logger.error(f"Error completing interview: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/interview/status', methods=['GET'])
def get_interview_status():
    """Get current interview status."""
    return jsonify({
        'status': 'success',
        'is_active': interview_state['is_active'],
        'current_question_index': interview_state['current_question_index'],
        'total_questions': len(interview_state['questions']),
        'total_score': interview_state['total_score']
    })

if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5001))
    print(f"🎤 Starting React Interview API server on port {port}")
    print(f"📚 API Endpoints:")
    print(f"  • GET  /health - Health check")
    print(f"  • POST /interview/start - Start interview")
    print(f"  • GET  /interview/question - Get current question")
    print(f"  • POST /interview/transcribe - Transcribe audio")
    print(f"  • POST /interview/submit - Submit answer")
    print(f"  • POST /interview/complete - Complete interview")
    print(f"  • GET  /interview/status - Get interview status")
    
    app.run(debug=True, host='0.0.0.0', port=port)

