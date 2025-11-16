"""
Complete API Server with Admin and Candidate Flows
Handles authentication, test management, and interview sessions
"""

import os
import sys
import logging
import tempfile
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from bson import ObjectId
from datetime import datetime

from gemini_client import GeminiClient
from speech_processor import SpeechProcessor
from database import (
    get_database, close_database, 
    UserModel, TestModel, TestAssignmentModel, TestResultModel
)
from auth import (
    hash_password, verify_password, generate_token, 
    token_required, admin_required, candidate_required
)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database connection
try:
    db = get_database()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")
    sys.exit(1)

# Interview session storage (in-memory for now)
active_sessions = {}

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


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.route('/auth/register', methods=['POST'])
def register():
    """Register a new user (admin or candidate)."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password', 'name', 'role']
        for field in required_fields:
            if field not in data:
                return jsonify({'status': 'error', 'error': f'{field} is required'}), 400
        
        email = data['email']
        password = data['password']
        name = data['name']
        role = data['role']
        
        # Validate role
        if role not in ['admin', 'candidate']:
            return jsonify({'status': 'error', 'error': 'Invalid role'}), 400
        
        # Check if user already exists
        existing_user = UserModel.find_by_email(email)
        if existing_user:
            return jsonify({'status': 'error', 'error': 'Email already registered'}), 400
        
        # Hash password and create user
        password_hash = hash_password(password)
        user = UserModel.create_user(email, password_hash, role, name)
        
        # Generate token
        token = generate_token(user['_id'], user['email'], user['role'])
        
        return jsonify({
            'status': 'success',
            'message': 'User registered successfully',
            'token': token,
            'user': {
                'id': str(user['_id']),
                'email': user['email'],
                'name': user['name'],
                'role': user['role']
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error during registration: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/auth/login', methods=['POST'])
def login():
    """Login user and return JWT token."""
    try:
        data = request.get_json()
        
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({'status': 'error', 'error': 'Email and password are required'}), 400
        
        email = data['email']
        password = data['password']
        
        # Find user
        user = UserModel.find_by_email(email)
        if not user:
            return jsonify({'status': 'error', 'error': 'Invalid credentials'}), 401
        
        # Verify password
        if not verify_password(password, user['password_hash']):
            return jsonify({'status': 'error', 'error': 'Invalid credentials'}), 401
        
        # Generate token
        token = generate_token(user['_id'], user['email'], user['role'])
        
        return jsonify({
            'status': 'success',
            'message': 'Login successful',
            'token': token,
            'user': {
                'id': str(user['_id']),
                'email': user['email'],
                'name': user['name'],
                'role': user['role']
            }
        })
        
    except Exception as e:
        logger.error(f"Error during login: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/auth/me', methods=['GET'])
@token_required
def get_current_user():
    """Get current user info."""
    user = request.current_user
    
    return jsonify({
        'status': 'success',
        'user': {
            'id': str(user['_id']),
            'email': user['email'],
            'name': user['name'],
            'role': user['role']
        }
    })


# ============================================================================
# ADMIN ENDPOINTS - Test Management
# ============================================================================

@app.route('/admin/tests/create', methods=['POST'])
@admin_required
def create_test():
    """Create a new test based on a prompt."""
    try:
        user = request.current_user
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['title', 'description', 'prompt']
        for field in required_fields:
            if field not in data:
                return jsonify({'status': 'error', 'error': f'{field} is required'}), 400
        
        title = data['title']
        description = data['description']
        prompt = data['prompt']
        total_questions = data.get('total_questions', 5)
        
        # Create test in database
        test = TestModel.create_test(
            title=title,
            description=description,
            prompt=prompt,
            created_by=user['_id'],
            total_questions=total_questions
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Test created successfully',
            'test': {
                'id': str(test['_id']),
                'title': test['title'],
                'description': test['description'],
                'prompt': test['prompt'],
                'total_questions': test['total_questions'],
                'created_at': test['created_at'].isoformat()
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating test: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/admin/tests', methods=['GET'])
@admin_required
def get_admin_tests():
    """Get all tests created by the admin."""
    try:
        user = request.current_user
        
        tests = TestModel.get_tests_by_admin(user['_id'])
        
        test_list = []
        for test in tests:
            test_list.append({
                'id': str(test['_id']),
                'title': test['title'],
                'description': test['description'],
                'prompt': test['prompt'],
                'total_questions': test['total_questions'],
                'created_at': test['created_at'].isoformat()
            })
        
        return jsonify({
            'status': 'success',
            'tests': test_list
        })
        
    except Exception as e:
        logger.error(f"Error getting tests: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/admin/candidates', methods=['GET'])
@admin_required
def get_candidates():
    """Get all candidates."""
    try:
        candidates = UserModel.get_all_candidates()
        
        candidate_list = []
        for candidate in candidates:
            candidate_list.append({
                'id': str(candidate['_id']),
                'email': candidate['email'],
                'name': candidate['name'],
                'created_at': candidate['created_at'].isoformat()
            })
        
        return jsonify({
            'status': 'success',
            'candidates': candidate_list
        })
        
    except Exception as e:
        logger.error(f"Error getting candidates: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/admin/tests/assign', methods=['POST'])
@admin_required
def assign_test():
    """Assign a test to a candidate."""
    try:
        user = request.current_user
        data = request.get_json()
        
        if not data or 'test_id' not in data or 'candidate_id' not in data:
            return jsonify({'status': 'error', 'error': 'test_id and candidate_id are required'}), 400
        
        test_id = data['test_id']
        candidate_id = data['candidate_id']
        
        # Verify test exists
        test = TestModel.find_by_id(test_id)
        if not test:
            return jsonify({'status': 'error', 'error': 'Test not found'}), 404
        
        # Verify candidate exists
        candidate = UserModel.find_by_id(candidate_id)
        if not candidate or candidate['role'] != 'candidate':
            return jsonify({'status': 'error', 'error': 'Candidate not found'}), 404
        
        # Assign test
        assignment = TestAssignmentModel.assign_test(test_id, candidate_id, user['_id'])
        
        if not assignment:
            return jsonify({'status': 'error', 'error': 'Test already assigned to this candidate'}), 400
        
        return jsonify({
            'status': 'success',
            'message': 'Test assigned successfully',
            'assignment': {
                'id': str(assignment['_id']),
                'test_id': str(assignment['test_id']),
                'candidate_id': str(assignment['candidate_id']),
                'status': assignment['status'],
                'assigned_at': assignment['assigned_at'].isoformat()
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error assigning test: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/admin/assignments', methods=['GET'])
@admin_required
def get_all_assignments():
    """Get all test assignments with details."""
    try:
        assignments = TestAssignmentModel.get_all_assignments()
        
        assignment_list = []
        for assignment in assignments:
            # Get test details
            test = TestModel.find_by_id(assignment['test_id'])
            # Get candidate details
            candidate = UserModel.find_by_id(assignment['candidate_id'])
            # Get result if completed
            result = TestResultModel.get_result_by_test_and_candidate(
                assignment['test_id'], 
                assignment['candidate_id']
            )
            
            assignment_data = {
                'id': str(assignment['_id']),
                'test': {
                    'id': str(test['_id']),
                    'title': test['title'],
                    'description': test['description']
                } if test else None,
                'candidate': {
                    'id': str(candidate['_id']),
                    'name': candidate['name'],
                    'email': candidate['email']
                } if candidate else None,
                'status': assignment['status'],
                'assigned_at': assignment['assigned_at'].isoformat()
            }
            
            if result:
                assignment_data['result'] = {
                    'total_score': result['total_score'],
                    'total_questions': result['total_questions'],
                    'percentage': result['percentage'],
                    'completed_at': result['completed_at'].isoformat()
                }
            
            assignment_list.append(assignment_data)
        
        return jsonify({
            'status': 'success',
            'assignments': assignment_list
        })
        
    except Exception as e:
        logger.error(f"Error getting assignments: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500


# ============================================================================
# CANDIDATE ENDPOINTS - Dashboard and Tests
# ============================================================================

@app.route('/candidate/dashboard', methods=['GET'])
@candidate_required
def get_candidate_dashboard():
    """Get candidate dashboard data."""
    try:
        user = request.current_user
        
        # Get assigned tests
        assignments = TestAssignmentModel.get_candidate_assignments(user['_id'])
        
        # Get completed results
        results = TestResultModel.get_candidate_results(user['_id'])
        
        # Build dashboard data
        assigned_tests = []
        for assignment in assignments:
            test = TestModel.find_by_id(assignment['test_id'])
            if not test:
                continue
            
            test_data = {
                'assignment_id': str(assignment['_id']),
                'test_id': str(test['_id']),
                'title': test['title'],
                'description': test['description'],
                'total_questions': test['total_questions'],
                'status': assignment['status'],
                'assigned_at': assignment['assigned_at'].isoformat()
            }
            
            # Check if there's a result
            result = TestResultModel.get_result_by_test_and_candidate(test['_id'], user['_id'])
            if result:
                test_data['result'] = {
                    'total_score': result['total_score'],
                    'total_questions': result['total_questions'],
                    'percentage': result['percentage'],
                    'completed_at': result['completed_at'].isoformat()
                }
            
            assigned_tests.append(test_data)
        
        # Calculate statistics
        total_tests = len(assignments)
        completed_tests = len([a for a in assignments if a['status'] == 'completed'])
        pending_tests = len([a for a in assignments if a['status'] == 'pending'])
        
        avg_score = 0
        if results:
            avg_score = sum([r['percentage'] for r in results]) / len(results)
        
        return jsonify({
            'status': 'success',
            'dashboard': {
                'stats': {
                    'total_tests': total_tests,
                    'completed_tests': completed_tests,
                    'pending_tests': pending_tests,
                    'average_score': round(avg_score, 2)
                },
                'assigned_tests': assigned_tests
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting dashboard: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500


# ============================================================================
# INTERVIEW SESSION ENDPOINTS
# ============================================================================

def generate_questions_from_prompt(prompt, total_questions):
    """Generate interview questions based on prompt using Gemini."""
    client = get_gemini_client()
    
    full_prompt = f"""You are an experienced technical interviewer. Generate exactly {total_questions} specific, detailed interview questions based on the following prompt:

{prompt}

IMPORTANT RULES:
1. Generate ACTUAL, SPECIFIC questions - not generic templates
2. Each question should be clear, detailed, and conversational
3. Questions should be suitable for a voice interview (easy to understand when spoken)
4. Each question should be 20-50 words long
5. Make questions practical and real-world focused
6. Do NOT use placeholders or generic formats

RESPOND ONLY with a JSON array of strings in this exact format:
["First specific question here?", "Second specific question here?", ...]

Do NOT include any other text, explanations, markdown, or code blocks - ONLY the JSON array.

Example of GOOD questions:
["Can you explain how the useState hook works and provide an example of when you would use it?", "What is the virtual DOM and how does React use it to improve performance?"]

Example of BAD questions (do NOT generate these):
["Question 1 about React", "Question based on: React fundamentals"]
"""
    
    try:
        response = client.send_message(full_prompt)
        import json
        
        logger.info(f"Gemini raw response: {response[:200]}")
        
        # Clean up response to extract JSON
        response = response.strip()
        if '```json' in response:
            response = response.split('```json')[1].split('```')[0].strip()
        elif '```' in response:
            response = response.split('```')[1].split('```')[0].strip()
        
        # Remove any leading/trailing text before the array
        if '[' in response and ']' in response:
            start = response.index('[')
            end = response.rindex(']') + 1
            response = response[start:end]
        
        questions = json.loads(response)
        
        if isinstance(questions, list) and len(questions) >= total_questions:
            logger.info(f"Successfully generated {len(questions)} questions: {questions[:total_questions]}")
            return questions[:total_questions]
        else:
            logger.warning(f"Invalid response format, got: {type(questions)} with {len(questions) if isinstance(questions, list) else 0} items")
            # Generate fallback questions using Gemini with a simpler prompt
            return generate_fallback_questions(prompt, total_questions)
    except Exception as e:
        logger.error(f"Error generating questions: {e}, response was: {response[:200] if 'response' in locals() else 'N/A'}")
        return generate_fallback_questions(prompt, total_questions)


def generate_fallback_questions(prompt, total_questions):
    """Generate fallback questions when main generation fails."""
    # Try one more time with a simpler approach
    client = get_gemini_client()
    
    try:
        questions = []
        for i in range(total_questions):
            simple_prompt = f"Generate one specific interview question about: {prompt}. Just give me the question text, nothing else."
            question = client.send_message(simple_prompt).strip()
            # Clean up the question
            question = question.replace('"', '').replace("'", '').strip()
            if not question.endswith('?'):
                question += '?'
            questions.append(question)
        
        if questions:
            logger.info(f"Generated fallback questions: {questions}")
            return questions
    except Exception as e:
        logger.error(f"Fallback generation also failed: {e}")
    
    # Last resort: return hard-coded but relevant questions based on common prompts
    logger.warning("Using hard-coded fallback questions")
    
    # Try to detect the topic from the prompt
    prompt_lower = prompt.lower()
    
    if 'react' in prompt_lower:
        default_questions = [
            "Can you explain what React hooks are and how the useState hook works?",
            "What is the difference between props and state in React?",
            "How does React's virtual DOM improve application performance?",
            "Can you describe the React component lifecycle?",
            "What are the key differences between class components and functional components in React?",
            "How would you optimize the performance of a large React application?",
            "What is prop drilling and how can you avoid it?",
            "Can you explain how useEffect works and provide a use case?",
            "What are React keys and why are they important?",
            "How do you handle forms in React?"
        ]
    elif 'javascript' in prompt_lower or 'js' in prompt_lower:
        default_questions = [
            "Can you explain how closures work in JavaScript?",
            "What is the difference between let, const, and var?",
            "How does asynchronous programming work in JavaScript?",
            "Can you explain the concept of promises?",
            "What is the event loop in JavaScript?",
            "How do you handle errors in JavaScript?",
            "What are arrow functions and how do they differ from regular functions?",
            "Can you explain prototypal inheritance?",
            "What is the difference between == and === in JavaScript?",
            "How does the 'this' keyword work in JavaScript?"
        ]
    elif 'python' in prompt_lower:
        default_questions = [
            "Can you explain how decorators work in Python?",
            "What is the difference between lists and tuples?",
            "How does memory management work in Python?",
            "Can you explain generators and iterators?",
            "What are list comprehensions and when would you use them?",
            "How do you handle exceptions in Python?",
            "What is the difference between deep copy and shallow copy?",
            "Can you explain how the GIL works?",
            "What are Python context managers?",
            "How does Python's import system work?"
        ]
    else:
        # Generic programming questions
        default_questions = [
            "Can you describe your experience with software development?",
            "How do you approach debugging complex issues?",
            "What design patterns are you familiar with?",
            "How do you ensure code quality in your projects?",
            "Can you explain your approach to testing?",
            "How do you stay updated with new technologies?",
            "What is your experience with version control systems?",
            "How do you handle technical debt?",
            "Can you describe a challenging project you worked on?",
            "What are your thoughts on code reviews?"
        ]
    
    return default_questions[:total_questions]


def evaluate_answer(question, answer):
    """Evaluate answer using Gemini and return score (0 or 1)."""
    client = get_gemini_client()
    
    prompt = f"""You are an interviewer evaluating a candidate's answer.

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


@app.route('/candidate/test/start', methods=['POST'])
@candidate_required
def start_test():
    """Start a test session."""
    try:
        user = request.current_user
        data = request.get_json()
        
        if not data or 'test_id' not in data:
            return jsonify({'status': 'error', 'error': 'test_id is required'}), 400
        
        test_id = data['test_id']
        
        # Verify test exists and is assigned to candidate
        assignment = TestAssignmentModel.get_assignment(test_id, user['_id'])
        if not assignment:
            return jsonify({'status': 'error', 'error': 'Test not assigned to you'}), 403
        
        # Get test details
        test = TestModel.find_by_id(test_id)
        if not test:
            return jsonify({'status': 'error', 'error': 'Test not found'}), 404
        
        # Generate questions based on test prompt
        questions = generate_questions_from_prompt(test['prompt'], test['total_questions'])
        
        # Create session
        session_id = f"{user['_id']}_{test_id}"
        active_sessions[session_id] = {
            'test_id': test_id,
            'candidate_id': str(user['_id']),
            'questions': questions,
            'answers': [],
            'scores': [],
            'current_question_index': 0,
            'total_score': 0
        }
        
        # Update assignment status
        TestAssignmentModel.update_status(assignment['_id'], 'in_progress')
        
        return jsonify({
            'status': 'success',
            'message': 'Test started',
            'session_id': session_id,
            'test_title': test['title'],
            'total_questions': len(questions),
            'first_question': questions[0] if questions else None
        })
        
    except Exception as e:
        logger.error(f"Error starting test: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/candidate/test/transcribe', methods=['POST'])
@candidate_required
def transcribe_audio():
    """Transcribe audio from the candidate."""
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


@app.route('/candidate/test/submit', methods=['POST'])
@candidate_required
def submit_answer():
    """Submit an answer for the current question."""
    try:
        user = request.current_user
        data = request.get_json()
        
        if not data or 'session_id' not in data or 'answer' not in data:
            return jsonify({'status': 'error', 'error': 'session_id and answer are required'}), 400
        
        session_id = data['session_id']
        answer = data['answer'].strip()
        
        # Get session
        if session_id not in active_sessions:
            return jsonify({'status': 'error', 'error': 'Invalid session'}), 400
        
        session = active_sessions[session_id]
        
        # Verify session belongs to user
        if session['candidate_id'] != str(user['_id']):
            return jsonify({'status': 'error', 'error': 'Unauthorized'}), 403
        
        index = session['current_question_index']
        
        if index >= len(session['questions']):
            return jsonify({'status': 'error', 'error': 'No more questions'}), 400
        
        question = session['questions'][index]
        
        # Evaluate the answer
        score = evaluate_answer(question, answer)
        
        # Store answer and score
        session['answers'].append(answer)
        session['scores'].append(score)
        session['total_score'] += score
        session['current_question_index'] += 1
        
        # Check if test is complete
        is_complete = session['current_question_index'] >= len(session['questions'])
        
        next_question = None
        if not is_complete:
            next_question = session['questions'][session['current_question_index']]
        
        return jsonify({
            'status': 'success',
            'score': score,
            'is_complete': is_complete,
            'next_question': next_question,
            'question_number': session['current_question_index'] + 1 if not is_complete else None,
            'total_questions': len(session['questions'])
        })
        
    except Exception as e:
        logger.error(f"Error submitting answer: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/candidate/test/complete', methods=['POST'])
@candidate_required
def complete_test():
    """Complete the test and save results."""
    try:
        user = request.current_user
        data = request.get_json()
        
        if not data or 'session_id' not in data:
            return jsonify({'status': 'error', 'error': 'session_id is required'}), 400
        
        session_id = data['session_id']
        
        # Get session
        if session_id not in active_sessions:
            return jsonify({'status': 'error', 'error': 'Invalid session'}), 400
        
        session = active_sessions[session_id]
        
        # Verify session belongs to user
        if session['candidate_id'] != str(user['_id']):
            return jsonify({'status': 'error', 'error': 'Unauthorized'}), 403
        
        # Save result to database
        result = TestResultModel.save_result(
            test_id=session['test_id'],
            candidate_id=user['_id'],
            questions=session['questions'],
            answers=session['answers'],
            scores=session['scores'],
            total_score=session['total_score']
        )
        
        # Update assignment status
        assignment = TestAssignmentModel.get_assignment(session['test_id'], user['_id'])
        if assignment:
            TestAssignmentModel.update_status(assignment['_id'], 'completed')
        
        # Generate closing message
        score = session['total_score']
        total = len(session['questions'])
        percentage = (score / total * 100) if total > 0 else 0
        
        closing_message = f"""Thank you for completing this test!

Your final score is {score} out of {total} ({percentage:.0f}%).

{'Excellent work! You demonstrated strong knowledge.' if percentage >= 80 else 
 'Good effort! Keep practicing to improve your skills.' if percentage >= 60 else
 'Thank you for your time. Consider reviewing the topics covered.'}

Best of luck with your development journey!"""
        
        # Clean up session
        del active_sessions[session_id]
        
        return jsonify({
            'status': 'success',
            'closing_message': closing_message,
            'result': {
                'final_score': score,
                'total_questions': total,
                'percentage': percentage,
                'questions': session['questions'],
                'answers': session['answers'],
                'scores': session['scores']
            }
        })
        
    except Exception as e:
        logger.error(f"Error completing test: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'Interview Management System'
    })


# ============================================================================
# STARTUP
# ============================================================================

if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5001))
    print(f"🚀 Starting Interview Management API server on port {port}")
    print(f"📚 API Endpoints:")
    print(f"  Authentication:")
    print(f"    • POST /auth/register - Register new user")
    print(f"    • POST /auth/login - Login user")
    print(f"    • GET  /auth/me - Get current user")
    print(f"  Admin:")
    print(f"    • POST /admin/tests/create - Create test")
    print(f"    • GET  /admin/tests - Get admin tests")
    print(f"    • GET  /admin/candidates - Get all candidates")
    print(f"    • POST /admin/tests/assign - Assign test to candidate")
    print(f"    • GET  /admin/assignments - Get all assignments")
    print(f"  Candidate:")
    print(f"    • GET  /candidate/dashboard - Get dashboard")
    print(f"    • POST /candidate/test/start - Start test")
    print(f"    • POST /candidate/test/transcribe - Transcribe audio")
    print(f"    • POST /candidate/test/submit - Submit answer")
    print(f"    • POST /candidate/test/complete - Complete test")
    
    try:
        app.run(debug=True, host='0.0.0.0', port=port)
    finally:
        close_database()

