# 🎯 Interview Management System

A comprehensive AI-powered interview platform with separate Admin and Candidate portals, featuring voice-based interview capabilities, test management, and MongoDB persistence.

## ✨ Features

### Admin Features
- 🔐 **Secure Authentication** - JWT-based auth system
- 📝 **Test Creation** - Create tests using AI prompts
- 👥 **Candidate Management** - View and manage registered candidates
- 📋 **Test Assignment** - Assign tests to specific candidates
- 📊 **Results Dashboard** - Track candidate performance and scores
- 🎯 **AI-Powered Questions** - Questions generated dynamically using Google Gemini

### Candidate Features
- 🎤 **Voice-Based Interviews** - Answer questions using your microphone
- 📊 **Personal Dashboard** - View assigned tests, scores, and statistics
- ⏳ **Test Progress Tracking** - See pending, in-progress, and completed tests
- 🎯 **Real-Time Transcription** - Automatic speech-to-text using Whisper
- ✅ **Instant Feedback** - AI-powered answer evaluation
- 📈 **Performance Analytics** - Average scores and detailed results

## 🏗️ Architecture

### Backend (Flask + Python)
```
backend/
├── api.py                # Main API server with all endpoints
├── auth.py               # JWT authentication utilities
├── database.py           # MongoDB models and operations
├── gemini_client.py      # Gemini AI integration
├── speech_processor.py   # Whisper speech-to-text
├── response_formatter.py # Response formatting utilities
├── requirements.txt      # Python dependencies
└── .env                  # Environment variables (create from .env.example)
```

### Frontend (React + Vite)
```
frontend/
├── src/
│   ├── App.jsx                    # Main app with routing
│   ├── AuthContext.jsx            # Authentication context
│   ├── pages/
│   │   ├── Login.jsx              # Login page
│   │   ├── Register.jsx           # Registration page
│   │   ├── AdminDashboard.jsx     # Admin portal
│   │   ├── CandidateDashboard.jsx # Candidate portal
│   │   └── TakeTest.jsx           # Test-taking interface
│   └── ...
├── package.json
└── vite.config.js
```

### Database (MongoDB)
Collections:
- **users** - Admin and candidate accounts
- **tests** - Created tests with AI prompts
- **test_assignments** - Test-to-candidate assignments
- **test_results** - Completed test results and scores

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- MongoDB (local or cloud instance)
- Google Gemini API key

### 1. MongoDB Setup

**Option A: Local MongoDB**
```bash
# Install MongoDB (macOS)
brew tap mongodb/brew
brew install mongodb-community@7.0
brew services start mongodb-community@7.0

# Verify it's running
mongo --version
```

**Option B: MongoDB Atlas (Cloud)**
1. Create account at https://www.mongodb.com/cloud/atlas
2. Create a free cluster
3. Get connection string
4. Update MONGO_URI in backend/.env

### 2. Backend Setup
```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file from example
cp .env.example .env

# Edit .env and add your credentials:
# - GOOGLE_API_KEY
# - MONGO_URI (if using MongoDB Atlas)
# - JWT_SECRET (generate a random string)

# Start the server
python api.py
```

The backend will run on `http://localhost:5001`

### 3. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will run on `http://localhost:5173`

## 📋 API Endpoints

### Authentication
- `POST /auth/register` - Register new user (admin or candidate)
- `POST /auth/login` - Login user
- `GET /auth/me` - Get current user info

### Admin Endpoints (Requires Admin Token)
- `POST /admin/tests/create` - Create a new test
- `GET /admin/tests` - Get all tests created by admin
- `GET /admin/candidates` - Get all registered candidates
- `POST /admin/tests/assign` - Assign test to candidate
- `GET /admin/assignments` - Get all test assignments with results

### Candidate Endpoints (Requires Candidate Token)
- `GET /candidate/dashboard` - Get dashboard with stats and tests
- `POST /candidate/test/start` - Start a test session
- `POST /candidate/test/transcribe` - Transcribe audio answer
- `POST /candidate/test/submit` - Submit answer for evaluation
- `POST /candidate/test/complete` - Complete test and save results

## 🔐 Environment Variables

### Backend (.env)
```env
# Gemini API
GOOGLE_API_KEY=your_gemini_api_key

# MongoDB
MONGO_URI=mongodb://localhost:27017/
DB_NAME=interview_system

# JWT
JWT_SECRET=your_secret_key_here

# Flask
FLASK_PORT=5001
DEBUG_MODE=true

# Whisper
WHISPER_MODEL_SIZE=base
DEVICE=cpu
```

### Frontend (.env)
```env
VITE_API_URL=http://localhost:5001
```

## 👥 Usage Flow

### Admin Workflow
1. **Register** as Admin
2. **Login** to Admin Dashboard
3. **Create Tests** using AI prompts
   - Example: "Generate React interview questions focusing on hooks and state management"
4. **View Candidates** who have registered
5. **Assign Tests** to specific candidates
6. **Track Results** as candidates complete tests

### Candidate Workflow
1. **Register** as Candidate
2. **Login** to Candidate Dashboard
3. **View Assigned Tests** and statistics
4. **Start Test** - Click on pending test
5. **Answer Questions** using voice:
   - Click microphone to start recording
   - Speak your answer
   - Click stop when done
   - Review transcription
   - Submit or retry
6. **View Results** - See scores and feedback
7. **Track Progress** on dashboard

## 🎨 Technology Stack

### Backend
- **Flask** - Web framework
- **MongoDB** - Database
- **PyMongo** - MongoDB driver
- **PyJWT** - JWT authentication
- **Bcrypt** - Password hashing
- **Google Gemini 2.0** - AI question generation and evaluation
- **Faster Whisper** - Speech-to-text transcription
- **Flask-CORS** - Cross-origin support

### Frontend
- **React 18** - UI framework
- **React Router** - Routing
- **Context API** - State management
- **MediaRecorder API** - Audio recording
- **Fetch API** - HTTP requests
- **CSS3** - Styling with animations

## 🔧 Development

### Running Tests
```bash
# Backend
cd backend
python -m pytest

# Frontend
cd frontend
npm run test
```

### Building for Production
```bash
# Frontend
cd frontend
npm run build

# Serve with nginx or any static server
```

## 📊 Database Schema

### Users Collection
```javascript
{
  _id: ObjectId,
  email: String,
  password_hash: String,
  role: String,  // 'admin' or 'candidate'
  name: String,
  created_at: Date,
  updated_at: Date
}
```

### Tests Collection
```javascript
{
  _id: ObjectId,
  title: String,
  description: String,
  prompt: String,  // AI prompt for questions
  created_by: ObjectId,  // Admin user ID
  total_questions: Number,
  created_at: Date,
  updated_at: Date
}
```

### Test Assignments Collection
```javascript
{
  _id: ObjectId,
  test_id: ObjectId,
  candidate_id: ObjectId,
  assigned_by: ObjectId,  // Admin user ID
  status: String,  // 'pending', 'in_progress', 'completed'
  assigned_at: Date
}
```

### Test Results Collection
```javascript
{
  _id: ObjectId,
  test_id: ObjectId,
  candidate_id: ObjectId,
  questions: [String],
  answers: [String],
  scores: [Number],
  total_score: Number,
  total_questions: Number,
  percentage: Number,
  completed_at: Date
}
```

## 🐛 Troubleshooting

### MongoDB Connection Issues
```bash
# Check if MongoDB is running
brew services list

# Restart MongoDB
brew services restart mongodb-community@7.0
```

### Port Already in Use
```bash
# Kill process on port 5001
lsof -ti:5001 | xargs kill -9

# Kill process on port 5173
lsof -ti:5173 | xargs kill -9
```

### Microphone Access Issues
- Ensure browser has microphone permissions
- Try HTTPS or localhost (HTTP is allowed for localhost)
- Check browser console for errors

## 📝 License
MIT License - Use freely for learning and projects.

## 🤝 Contributing
Contributions are welcome! Please feel free to submit issues or pull requests.

---

**Built with ❤️ using React, Flask, MongoDB, and AI**

# Al_Interview_App
