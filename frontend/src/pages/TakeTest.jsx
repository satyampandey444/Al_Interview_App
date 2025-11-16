import React, { useState, useRef, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';
import './TakeTest.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5001';

function TakeTest() {
  const { testId } = useParams();
  const { token } = useAuth();
  const navigate = useNavigate();
  
  const [sessionId, setSessionId] = useState(null);
  const [testTitle, setTestTitle] = useState('');
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [questionNumber, setQuestionNumber] = useState(0);
  const [totalQuestions, setTotalQuestions] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [transcribedText, setTranscribedText] = useState('');
  const [showControls, setShowControls] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [score, setScore] = useState(0);
  const [isComplete, setIsComplete] = useState(false);
  const [closingMessage, setClosingMessage] = useState('');
  const [questionHistory, setQuestionHistory] = useState([]);
  const [error, setError] = useState('');
  const [testStarted, setTestStarted] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [canAnswer, setCanAnswer] = useState(false);
  const [welcomeMessage, setWelcomeMessage] = useState('');
  const [showWelcome, setShowWelcome] = useState(true);
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const speechSynthRef = useRef(window.speechSynthesis);
  const hasSpokenWelcome = useRef(false);

  // Text-to-Speech function with cooler voice
  const speakText = (text, onComplete) => {
    speechSynthRef.current.cancel();
    
    const utterance = new SpeechSynthesisUtterance(text);
    
    const voices = speechSynthRef.current.getVoices();
    // Prefer professional, deep voices - cooler sounding
    const preferredVoices = [
      'Google UK English Male',
      'Google US English Male', 
      'Microsoft David',
      'Alex',
      'Daniel',
      'Google UK English Female',
      'Samantha',
      'Karen'
    ];
    
    let selectedVoice = voices.find(voice => 
      preferredVoices.some(pref => voice.name.includes(pref))
    );
    
    if (!selectedVoice) {
      selectedVoice = voices.find(voice => voice.lang.startsWith('en') && voice.name.includes('Male'));
    }
    
    if (!selectedVoice) {
      selectedVoice = voices.find(voice => voice.lang.startsWith('en'));
    }
    
    if (selectedVoice) {
      utterance.voice = selectedVoice;
    }
    
    // Cooler voice settings - slightly slower and deeper
    utterance.rate = 0.85;
    utterance.pitch = 0.9;
    utterance.volume = 1.0;
    
    utterance.onstart = () => {
      setIsSpeaking(true);
      setCanAnswer(false);
    };
    
    utterance.onend = () => {
      setIsSpeaking(false);
      setCanAnswer(true);
      if (onComplete) onComplete();
    };
    
    utterance.onerror = () => {
      setIsSpeaking(false);
      setCanAnswer(true);
    };
    
    speechSynthRef.current.speak(utterance);
  };

  // Load voices
  useEffect(() => {
    const loadVoices = () => {
      speechSynthRef.current.getVoices();
    };
    
    loadVoices();
    if (speechSynthRef.current.onvoiceschanged !== undefined) {
      speechSynthRef.current.onvoiceschanged = loadVoices;
    }
  }, []);

  useEffect(() => {
    if (!testStarted) {
      startTest();
    }
  }, []);

  // Speak welcome and first question
  useEffect(() => {
    if (welcomeMessage && questionNumber === 1 && !hasSpokenWelcome.current && testStarted) {
      hasSpokenWelcome.current = true;
      speakText(welcomeMessage, () => {
        setTimeout(() => {
          setShowWelcome(false);
          if (currentQuestion) {
            speakText(currentQuestion);
          }
        }, 1000);
      });
    }
  }, [welcomeMessage, questionNumber, testStarted, currentQuestion]);

  // Speak question when it changes (for subsequent questions)
  useEffect(() => {
    if (currentQuestion && !showControls && questionNumber > 1 && !showWelcome) {
      speakText(currentQuestion);
    }
  }, [currentQuestion, questionNumber, showControls, showWelcome]);

  // Cleanup
  useEffect(() => {
    return () => {
      speechSynthRef.current.cancel();
    };
  }, []);

  const startTest = async () => {
    try {
      setIsProcessing(true);
      setError('');
      
      const response = await fetch(`${API_URL}/candidate/test/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ test_id: testId })
      });
      
      const data = await response.json();
      
      if (data.status === 'success') {
        setSessionId(data.session_id);
        setTestTitle(data.test_title);
        setCurrentQuestion(data.first_question);
        setTotalQuestions(data.total_questions);
        setQuestionNumber(1);
        setTestStarted(true);
        
        // Generate welcome message
        const welcome = `Welcome to your ${data.test_title}! I'm excited to evaluate your knowledge. This test has ${data.total_questions} questions. Take your time with each answer, and feel free to explain your reasoning. Let's begin!`;
        setWelcomeMessage(welcome);
      } else {
        setError(data.error || 'Failed to start test');
        setTimeout(() => navigate('/candidate'), 3000);
      }
    } catch (error) {
      console.error('Error starting test:', error);
      setError('Failed to start test');
      setTimeout(() => navigate('/candidate'), 3000);
    } finally {
      setIsProcessing(false);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      mediaRecorderRef.current = new MediaRecorder(stream, {
        mimeType: 'audio/webm'
      });
      
      audioChunksRef.current = [];
      
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        await transcribeAudio(audioBlob);
        
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorderRef.current.start();
      setIsRecording(true);
      setTranscribedText('');
      setShowControls(false);
      
    } catch (error) {
      console.error('Error starting recording:', error);
      setError('Failed to access microphone. Please allow microphone access.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setIsProcessing(true);
    }
  };

  const transcribeAudio = async (audioBlob) => {
    try {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.webm');
      
      const response = await fetch(`${API_URL}/candidate/test/transcribe`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });
      
      const data = await response.json();
      
      if (data.status === 'success') {
        setTranscribedText(data.transcription);
        setShowControls(true);
      } else {
        setError(data.error || 'Failed to transcribe audio');
      }
    } catch (error) {
      console.error('Error transcribing audio:', error);
      setError('Failed to transcribe audio');
    } finally {
      setIsProcessing(false);
    }
  };

  const submitAnswer = async () => {
    try {
      setIsProcessing(true);
      setError('');
      
      const response = await fetch(`${API_URL}/candidate/test/submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          session_id: sessionId,
          answer: transcribedText
        })
      });
      
      const data = await response.json();
      
      if (data.status === 'success') {
        setScore(prevScore => prevScore + data.score);
        
        setQuestionHistory(prev => [...prev, {
          question: currentQuestion,
          answer: transcribedText,
          score: data.score
        }]);
        
        setTranscribedText('');
        setShowControls(false);
        
        if (data.is_complete) {
          completeTest();
        } else {
          setCurrentQuestion(data.next_question);
          setQuestionNumber(data.question_number);
        }
      } else {
        setError(data.error || 'Failed to submit answer');
      }
    } catch (error) {
      console.error('Error submitting answer:', error);
      setError('Failed to submit answer');
    } finally {
      setIsProcessing(false);
    }
  };

  const retryRecording = () => {
    setTranscribedText('');
    setShowControls(false);
    setCanAnswer(true);
  };

  const completeTest = async () => {
    try {
      const response = await fetch(`${API_URL}/candidate/test/complete`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ session_id: sessionId })
      });
      
      const data = await response.json();
      
      if (data.status === 'success') {
        setClosingMessage(data.closing_message);
        setIsComplete(true);
        setScore(data.result.final_score);
        setQuestionHistory(data.result.questions.map((q, i) => ({
          question: q,
          answer: data.result.answers[i],
          score: data.result.scores[i]
        })));
        
        // Speak closing message
        setTimeout(() => {
          speakText(data.closing_message);
        }, 500);
      }
    } catch (error) {
      console.error('Error completing test:', error);
      setError('Failed to complete test');
    }
  };

  const returnToDashboard = () => {
    speechSynthRef.current.cancel();
    navigate('/candidate');
  };

  if (!testStarted && isProcessing) {
    return (
      <div className="test-container">
        <div className="loading-screen">
          <div className="spinner"></div>
          <p>Starting your test...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="test-container">
      {!isComplete ? (
        <>
          {/* Progress Bar at Top */}
          <div className="progress-header">
            <div className="progress-info">
              <span className="progress-label">Question {questionNumber} of {totalQuestions}</span>
              <span className="score-label">Score: {score}/{totalQuestions}</span>
            </div>
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${(questionNumber / totalQuestions) * 100}%` }}
              ></div>
            </div>
          </div>

          <main className="test-main">
            {error && (
              <div className="error-message">
                <p>⚠️ {error}</p>
                <button onClick={() => setError('')}>✕</button>
              </div>
            )}

            {/* Welcome Message */}
            {showWelcome && welcomeMessage && (
              <div className="welcome-overlay">
                <div className="welcome-content">
                  <h1>Welcome to {testTitle}!</h1>
                  <p className="welcome-text">{welcomeMessage}</p>
                  {isSpeaking && (
                    <div className="speaking-indicator">
                      <span className="pulse-dot"></span>
                      <span>AI is speaking...</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Question Display Section */}
            {!showWelcome && (
              <div className="question-display">
                <div className="question-badge">Question {questionNumber}</div>
                <h2 className="question-text">{currentQuestion}</h2>
              </div>
            )}

            {/* Two Section Layout: Interviewer (Left) & Candidate (Right) */}
            {!showWelcome && (
              <div className="interview-layout">
                {/* Left Side - AI Interviewer */}
                <div className="interviewer-section">
                  <div className="avatar-container">
                    <img src="/interviewer.png" alt="AI Interviewer" className="avatar-image" />
                    {isSpeaking && (
                      <div className="avatar-status speaking">
                        <span className="pulse-dot"></span>
                        Speaking...
                      </div>
                    )}
                  </div>
                  <h3>AI Interviewer</h3>
                  {isSpeaking && (
                    <p className="status-text">Asking question...</p>
                  )}
                  {canAnswer && !isRecording && (
                    <p className="status-text">Waiting for your answer...</p>
                  )}
                </div>

                {/* Right Side - Candidate */}
                <div className="candidate-section">
                  <div className="avatar-container">
                    <img src="/candidate.png" alt="Candidate" className="avatar-image" />
                    {isRecording && (
                      <div className="avatar-status recording">
                        <span className="pulse-dot"></span>
                        Recording...
                      </div>
                    )}
                  </div>
                  <h3>You (Candidate)</h3>
                  
                  {/* Answer Controls */}
                  <div className="answer-controls">
                    {!showControls ? (
                      <>
                        {!canAnswer && !isRecording && !isProcessing && (
                          <div className="waiting-state">
                            <p>Please wait for the AI to finish speaking...</p>
                          </div>
                        )}
                        
                        {canAnswer && !isRecording && !isProcessing && (
                          <button
                            className="mic-button"
                            onClick={startRecording}
                          >
                            🎤 Click to Answer
                          </button>
                        )}
                        
                        {isRecording && (
                          <button
                            className="stop-button"
                            onClick={stopRecording}
                          >
                            ⏹ Stop Recording
                          </button>
                        )}
                        
                        {isProcessing && (
                          <div className="processing-state">
                            <div className="spinner"></div>
                            <p>Processing your answer...</p>
                          </div>
                        )}
                      </>
                    ) : (
                      <div className="transcription-display">
                        <h4>Your Answer:</h4>
                        <div className="transcribed-text">
                          {transcribedText}
                        </div>
                        <div className="action-buttons">
                          <button
                            className="submit-button"
                            onClick={submitAnswer}
                            disabled={isProcessing}
                          >
                            Submit Answer
                          </button>
                          <button
                            className="retry-button"
                            onClick={retryRecording}
                            disabled={isProcessing}
                          >
                            Retry
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </main>
        </>
      ) : (
        <div className="completion-screen">
          <div className="completion-header">
            <h1>🎉 Test Complete!</h1>
          </div>

          <div className="score-display">
            <div className="final-score">
              <h2>Your Score</h2>
              <div className="score-circle">
                <span className="score-number">{score}</span>
                <span className="score-separator">/</span>
                <span className="score-total">{totalQuestions}</span>
              </div>
              <div className="score-percentage">
                {Math.round((score / totalQuestions) * 100)}%
              </div>
            </div>

            <div className="closing-message">
              <p>{closingMessage}</p>
            </div>
          </div>

          <div className="review-section">
            <h2>Question Review</h2>
            {questionHistory.map((item, index) => (
              <div key={index} className="review-item">
                <div className="review-header">
                  <h3>Question {index + 1}</h3>
                  <span className={`score-badge ${item.score === 1 ? 'correct' : 'incorrect'}`}>
                    {item.score === 1 ? '✓ Correct' : '✗ Incorrect'}
                  </span>
                </div>
                <p className="review-question">{item.question}</p>
                <div className="review-answer">
                  <strong>Your answer:</strong>
                  <p>{item.answer}</p>
                </div>
              </div>
            ))}
          </div>

          <button
            className="return-button"
            onClick={returnToDashboard}
          >
            Return to Dashboard
          </button>
        </div>
      )}
    </div>
  );
}

export default TakeTest;

