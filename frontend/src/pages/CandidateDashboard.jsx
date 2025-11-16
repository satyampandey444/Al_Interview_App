import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';
import './Dashboard.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5001';

function CandidateDashboard() {
  const { user, token, logout } = useAuth();
  const navigate = useNavigate();
  
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`${API_URL}/candidate/dashboard`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await response.json();
      if (data.status === 'success') {
        setDashboardData(data.dashboard);
      } else {
        setError(data.error);
      }
    } catch (err) {
      setError('Failed to fetch dashboard data');
    }
    setLoading(false);
  };

  const handleStartTest = (testId) => {
    navigate(`/candidate/test/${testId}`);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  if (loading) {
    return (
      <div className="dashboard-container">
        <div className="loading-screen">
          <div className="spinner"></div>
          <p>Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <div className="header-content">
          <h1>👨‍🎓 Candidate Dashboard</h1>
          <div className="header-actions">
            <span className="user-info">Welcome, {user?.name}</span>
            <button onClick={handleLogout} className="logout-button">Logout</button>
          </div>
        </div>
      </header>

      <div className="dashboard-main">
        {error && (
          <div className="error-banner">
            <p>⚠️ {error}</p>
            <button onClick={() => setError('')}>✕</button>
          </div>
        )}

        {/* Statistics Cards */}
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon">📝</div>
            <div className="stat-info">
              <h3>{dashboardData?.stats.total_tests || 0}</h3>
              <p>Total Tests</p>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">✅</div>
            <div className="stat-info">
              <h3>{dashboardData?.stats.completed_tests || 0}</h3>
              <p>Completed</p>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">⏳</div>
            <div className="stat-info">
              <h3>{dashboardData?.stats.pending_tests || 0}</h3>
              <p>Pending</p>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">⭐</div>
            <div className="stat-info">
              <h3>{dashboardData?.stats.average_score.toFixed(1) || 0}%</h3>
              <p>Average Score</p>
            </div>
          </div>
        </div>

        {/* Assigned Tests */}
        <div className="section">
          <h2>Your Tests</h2>
          
          {!dashboardData?.assigned_tests || dashboardData.assigned_tests.length === 0 ? (
            <div className="empty-state">
              <p>No tests assigned yet. Check back later!</p>
            </div>
          ) : (
            <div className="tests-list">
              {dashboardData.assigned_tests.map(test => (
                <div key={test.assignment_id} className="test-item">
                  <div className="test-item-header">
                    <h3>{test.title}</h3>
                    <span className={`status-badge ${test.status}`}>
                      {test.status}
                    </span>
                  </div>
                  
                  <p className="test-description">{test.description}</p>
                  
                  <div className="test-meta">
                    <span>📊 {test.total_questions} questions</span>
                    <span>📅 Assigned: {new Date(test.assigned_at).toLocaleDateString()}</span>
                  </div>
                  
                  {test.result ? (
                    <div className="test-result">
                      <div className="result-score">
                        <strong>Your Score: </strong>
                        <span className="score-highlight">
                          {test.result.total_score}/{test.result.total_questions}
                        </span>
                        <span className="percentage">
                          ({test.result.percentage.toFixed(0)}%)
                        </span>
                      </div>
                      <div className="result-date">
                        Completed on {new Date(test.result.completed_at).toLocaleDateString()}
                      </div>
                    </div>
                  ) : test.status === 'pending' ? (
                    <button
                      className="start-test-button"
                      onClick={() => handleStartTest(test.test_id)}
                    >
                      Start Test
                    </button>
                  ) : test.status === 'in_progress' ? (
                    <button
                      className="continue-test-button"
                      onClick={() => handleStartTest(test.test_id)}
                    >
                      Continue Test
                    </button>
                  ) : null}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default CandidateDashboard;

