import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';
import './Dashboard.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5001';

function AdminDashboard() {
  const { user, token, logout } = useAuth();
  const navigate = useNavigate();
  
  const [activeTab, setActiveTab] = useState('tests');
  const [tests, setTests] = useState([]);
  const [candidates, setCandidates] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Create Test Form
  const [showCreateTest, setShowCreateTest] = useState(false);
  const [testTitle, setTestTitle] = useState('');
  const [testDescription, setTestDescription] = useState('');
  const [testPrompt, setTestPrompt] = useState('');
  const [totalQuestions, setTotalQuestions] = useState(5);
  
  // Assignment Form
  const [showAssignTest, setShowAssignTest] = useState(false);
  const [selectedTestId, setSelectedTestId] = useState('');
  const [selectedCandidateId, setSelectedCandidateId] = useState('');
  
  // Result Details
  const [showResultDetails, setShowResultDetails] = useState(false);
  const [selectedResult, setSelectedResult] = useState(null);

  useEffect(() => {
    if (activeTab === 'tests') {
      fetchTests();
    } else if (activeTab === 'candidates') {
      fetchCandidates();
    } else if (activeTab === 'assignments') {
      fetchAssignments();
    }
  }, [activeTab]);

  const fetchTests = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`${API_URL}/admin/tests`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await response.json();
      if (data.status === 'success') {
        setTests(data.tests);
      } else {
        setError(data.error);
      }
    } catch (err) {
      setError('Failed to fetch tests');
    }
    setLoading(false);
  };

  const fetchCandidates = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`${API_URL}/admin/candidates`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await response.json();
      if (data.status === 'success') {
        setCandidates(data.candidates);
      } else {
        setError(data.error);
      }
    } catch (err) {
      setError('Failed to fetch candidates');
    }
    setLoading(false);
  };

  const fetchAssignments = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`${API_URL}/admin/assignments`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await response.json();
      if (data.status === 'success') {
        setAssignments(data.assignments);
      } else {
        setError(data.error);
      }
    } catch (err) {
      setError('Failed to fetch assignments');
    }
    setLoading(false);
  };

  const handleCreateTest = async (e) => {
    e.preventDefault();
    setError('');
    
    try {
      const response = await fetch(`${API_URL}/admin/tests/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          title: testTitle,
          description: testDescription,
          prompt: testPrompt,
          total_questions: totalQuestions
        })
      });
      
      const data = await response.json();
      
      if (data.status === 'success') {
        setShowCreateTest(false);
        setTestTitle('');
        setTestDescription('');
        setTestPrompt('');
        setTotalQuestions(5);
        fetchTests();
        alert('Test created successfully!');
      } else {
        setError(data.error);
      }
    } catch (err) {
      setError('Failed to create test');
    }
  };

  const handleAssignTest = async (e) => {
    e.preventDefault();
    setError('');
    
    try {
      const response = await fetch(`${API_URL}/admin/tests/assign`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          test_id: selectedTestId,
          candidate_id: selectedCandidateId
        })
      });
      
      const data = await response.json();
      
      if (data.status === 'success') {
        setShowAssignTest(false);
        setSelectedTestId('');
        setSelectedCandidateId('');
        alert('Test assigned successfully!');
        if (activeTab === 'assignments') {
          fetchAssignments();
        }
      } else {
        setError(data.error);
      }
    } catch (err) {
      setError('Failed to assign test');
    }
  };

  const openAssignDialog = () => {
    setShowAssignTest(true);
    // Fetch both tests and candidates if not already loaded
    if (tests.length === 0) fetchTests();
    if (candidates.length === 0) fetchCandidates();
  };

  const showResultDetailsModal = (result) => {
    setSelectedResult(result);
    setShowResultDetails(true);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <div className="header-content">
          <h1>👨‍💼 Admin Dashboard</h1>
          <div className="header-actions">
            <span className="user-info">Welcome, {user?.name}</span>
            <button onClick={handleLogout} className="logout-button">Logout</button>
          </div>
        </div>
      </header>

      <div className="dashboard-main">
        <nav className="dashboard-nav">
          <button
            className={`nav-button ${activeTab === 'tests' ? 'active' : ''}`}
            onClick={() => setActiveTab('tests')}
          >
            📝 Tests
          </button>
          <button
            className={`nav-button ${activeTab === 'candidates' ? 'active' : ''}`}
            onClick={() => setActiveTab('candidates')}
          >
            👥 Candidates
          </button>
          <button
            className={`nav-button ${activeTab === 'assignments' ? 'active' : ''}`}
            onClick={() => setActiveTab('assignments')}
          >
            📋 Assignments
          </button>
        </nav>

        <div className="dashboard-content">
          {error && (
            <div className="error-banner">
              <p>⚠️ {error}</p>
              <button onClick={() => setError('')}>✕</button>
            </div>
          )}

          {/* Tests Tab */}
          {activeTab === 'tests' && (
            <div className="tab-content">
              <div className="tab-header">
                <h2>Your Tests</h2>
                <button
                  className="primary-button"
                  onClick={() => setShowCreateTest(true)}
                >
                  + Create New Test
                </button>
              </div>

              {loading ? (
                <div className="loading">Loading tests...</div>
              ) : tests.length === 0 ? (
                <div className="empty-state">
                  <p>No tests created yet. Create your first test!</p>
                </div>
              ) : (
                <div className="card-grid">
                  {tests.map(test => (
                    <div key={test.id} className="test-card">
                      <h3>{test.title}</h3>
                      <p className="test-description">{test.description}</p>
                      <div className="test-meta">
                        <span>📊 {test.total_questions} questions</span>
                        <span>📅 {new Date(test.created_at).toLocaleDateString()}</span>
                      </div>
                      <div className="test-prompt">
                        <strong>Prompt:</strong>
                        <p>{test.prompt}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Candidates Tab */}
          {activeTab === 'candidates' && (
            <div className="tab-content">
              <div className="tab-header">
                <h2>Registered Candidates</h2>
                <button
                  className="primary-button"
                  onClick={openAssignDialog}
                >
                  + Assign Test
                </button>
              </div>

              {loading ? (
                <div className="loading">Loading candidates...</div>
              ) : candidates.length === 0 ? (
                <div className="empty-state">
                  <p>No candidates registered yet.</p>
                </div>
              ) : (
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Registered On</th>
                      </tr>
                    </thead>
                    <tbody>
                      {candidates.map(candidate => (
                        <tr key={candidate.id}>
                          <td>{candidate.name}</td>
                          <td>{candidate.email}</td>
                          <td>{new Date(candidate.created_at).toLocaleDateString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* Assignments Tab */}
          {activeTab === 'assignments' && (
            <div className="tab-content">
              <div className="tab-header">
                <h2>Test Assignments</h2>
                <button
                  className="primary-button"
                  onClick={openAssignDialog}
                >
                  + Assign Test
                </button>
              </div>

              {loading ? (
                <div className="loading">Loading assignments...</div>
              ) : assignments.length === 0 ? (
                <div className="empty-state">
                  <p>No tests assigned yet. Assign a test to a candidate!</p>
                </div>
              ) : (
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Test</th>
                        <th>Candidate</th>
                        <th>Status</th>
                        <th>Assigned On</th>
                        <th>Correct</th>
                        <th>Total</th>
                        <th>Score</th>
                        <th>Grade</th>
                      </tr>
                    </thead>
                    <tbody>
                      {assignments.map(assignment => (
                        <tr key={assignment.id}>
                          <td>{assignment.test?.title || 'N/A'}</td>
                          <td>
                            <div>
                              <div>{assignment.candidate?.name || 'N/A'}</div>
                              <small>{assignment.candidate?.email || ''}</small>
                            </div>
                          </td>
                          <td>
                            <span className={`status-badge ${assignment.status}`}>
                              {assignment.status}
                            </span>
                          </td>
                          <td>{new Date(assignment.assigned_at).toLocaleDateString()}</td>
                          <td className="result-cell">
                            {assignment.result ? (
                              <span className="correct-questions">
                                {assignment.result.total_score}
                              </span>
                            ) : (
                              <span className="no-result">-</span>
                            )}
                          </td>
                          <td className="result-cell">
                            {assignment.result ? (
                              <span className="total-questions">
                                {assignment.result.total_questions}
                              </span>
                            ) : (
                              <span className="no-result">-</span>
                            )}
                          </td>
                          <td className="result-cell">
                            {assignment.result ? (
                              <span 
                                className="percentage-display clickable-result"
                                onClick={() => showResultDetailsModal(assignment.result)}
                                title="Click to view detailed results"
                              >
                                {assignment.result.percentage.toFixed(0)}%
                              </span>
                            ) : (
                              <span className="no-result">-</span>
                            )}
                          </td>
                          <td className="result-cell">
                            {assignment.result ? (
                              <span className={`grade-badge ${assignment.result.percentage >= 70 ? 'pass' : 
                                 assignment.result.percentage >= 50 ? 'average' : 'fail'}`}>
                                {assignment.result.percentage >= 70 ? 'Pass' : 
                                 assignment.result.percentage >= 50 ? 'Average' : 'Fail'}
                              </span>
                            ) : (
                              <span className="no-result">-</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Create Test Modal */}
      {showCreateTest && (
        <div className="modal-overlay" onClick={() => setShowCreateTest(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Create New Test</h2>
              <button onClick={() => setShowCreateTest(false)} className="close-button">✕</button>
            </div>
            <form onSubmit={handleCreateTest}>
              <div className="form-group">
                <label>Test Title *</label>
                <input
                  type="text"
                  value={testTitle}
                  onChange={(e) => setTestTitle(e.target.value)}
                  required
                  placeholder="e.g., React Advanced Concepts"
                />
              </div>
              <div className="form-group">
                <label>Description *</label>
                <textarea
                  value={testDescription}
                  onChange={(e) => setTestDescription(e.target.value)}
                  required
                  placeholder="Brief description of the test"
                  rows="3"
                />
              </div>
              <div className="form-group">
                <label>AI Prompt for Questions *</label>
                <textarea
                  value={testPrompt}
                  onChange={(e) => setTestPrompt(e.target.value)}
                  required
                  placeholder="e.g., Generate questions about React hooks, state management, and performance optimization"
                  rows="4"
                />
              </div>
              <div className="form-group">
                <label>Number of Questions</label>
                <input
                  type="number"
                  value={totalQuestions}
                  onChange={(e) => setTotalQuestions(parseInt(e.target.value))}
                  min="1"
                  max="20"
                  required
                />
              </div>
              <div className="modal-actions">
                <button type="button" onClick={() => setShowCreateTest(false)} className="secondary-button">
                  Cancel
                </button>
                <button type="submit" className="primary-button">
                  Create Test
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Assign Test Modal */}
      {showAssignTest && (
        <div className="modal-overlay" onClick={() => setShowAssignTest(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Assign Test to Candidate</h2>
              <button onClick={() => setShowAssignTest(false)} className="close-button">✕</button>
            </div>
            <form onSubmit={handleAssignTest}>
              <div className="form-group">
                <label>Select Test *</label>
                <select
                  value={selectedTestId}
                  onChange={(e) => setSelectedTestId(e.target.value)}
                  required
                >
                  <option value="">-- Choose a test --</option>
                  {tests.map(test => (
                    <option key={test.id} value={test.id}>
                      {test.title}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Select Candidate *</label>
                <select
                  value={selectedCandidateId}
                  onChange={(e) => setSelectedCandidateId(e.target.value)}
                  required
                >
                  <option value="">-- Choose a candidate --</option>
                  {candidates.map(candidate => (
                    <option key={candidate.id} value={candidate.id}>
                      {candidate.name} ({candidate.email})
                    </option>
                  ))}
                </select>
              </div>
              <div className="modal-actions">
                <button type="button" onClick={() => setShowAssignTest(false)} className="secondary-button">
                  Cancel
                </button>
                <button type="submit" className="primary-button">
                  Assign Test
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Result Details Modal */}
      {showResultDetails && selectedResult && (
        <div className="modal-overlay" onClick={() => setShowResultDetails(false)}>
          <div className="modal-content result-details-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Test Result Details</h2>
              <button onClick={() => setShowResultDetails(false)} className="close-button">✕</button>
            </div>
            <div className="result-details-content">
              <div className="result-summary">
                <div className="summary-card">
                  <h3>Overall Score</h3>
                  <div className="score-display-large">
                    {selectedResult.total_score}/{selectedResult.total_questions}
                  </div>
                  <div className="percentage-display-large">
                    {selectedResult.percentage.toFixed(1)}%
                  </div>
                  <div className="performance-status">
                    {selectedResult.percentage >= 70 ? '🎉 Excellent Performance!' : 
                     selectedResult.percentage >= 50 ? '👍 Good Performance' : '📚 Needs Improvement'}
                  </div>
                </div>
              </div>
              
              {selectedResult.questions && selectedResult.questions.length > 0 && (
                <div className="questions-breakdown">
                  <h3>Question-by-Question Breakdown</h3>
                  <div className="questions-list">
                    {selectedResult.questions.map((question, index) => (
                      <div key={index} className="question-result-item">
                        <div className="question-header">
                          <span className="question-number">Q{index + 1}</span>
                          <span className={`question-score ${question.correct ? 'correct' : 'incorrect'}`}>
                            {question.correct ? '✅ Correct' : '❌ Incorrect'}
                          </span>
                        </div>
                        <div className="question-text">
                          {question.question}
                        </div>
                        {question.answer && (
                          <div className="candidate-answer">
                            <strong>Answer:</strong> {question.answer}
                          </div>
                        )}
                        {question.feedback && (
                          <div className="answer-feedback">
                            <strong>Feedback:</strong> {question.feedback}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
            <div className="modal-actions">
              <button onClick={() => setShowResultDetails(false)} className="primary-button">
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default AdminDashboard;

