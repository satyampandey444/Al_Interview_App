
"""
MongoDB Database Connection and Models
"""

import os
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
import logging
from pymongo import MongoClient
import certifi

logger = logging.getLogger(__name__)

# MongoDB connection
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
DB_NAME = os.getenv('DB_NAME', 'interview_system')

client = None
db = None

def get_database():
    """Get or create database connection."""
    global client, db

    if db is None:
        try:
            import certifi
            client = MongoClient(
                MONGO_URI,
                tls=True,
                tlsCAFile=certifi.where()
            )
            db = client[DB_NAME]

            # Test connection
            client.admin.command('ping')
            logger.info(f"Connected to MongoDB database: {DB_NAME}")

            # Create indexes
            db.users.create_index("email", unique=True)
            db.users.create_index("role")
            db.tests.create_index("created_by")
            db.test_assignments.create_index(
                [("candidate_id", 1), ("test_id", 1)],
                unique=True
            )
            db.test_results.create_index(
                [("candidate_id", 1), ("test_id", 1)]
            )

        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    return db


def close_database():
    """Close database connection."""
    global client
    if client:
        client.close()
        logger.info("MongoDB connection closed")


class UserModel:
    """User model for authentication and role management."""
    
    @staticmethod
    def create_user(email, password_hash, role, name):
        """Create a new user."""
        db = get_database()
        
        user = {
            'email': email.lower(),
            'password_hash': password_hash,
            'role': role,  # 'admin' or 'candidate'
            'name': name,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = db.users.insert_one(user)
        user['_id'] = result.inserted_id
        return user
    
    @staticmethod
    def find_by_email(email):
        """Find user by email."""
        db = get_database()
        return db.users.find_one({'email': email.lower()})
    
    @staticmethod
    def find_by_id(user_id):
        """Find user by ID."""
        db = get_database()
        return db.users.find_one({'_id': ObjectId(user_id)})
    
    @staticmethod
    def get_all_candidates():
        """Get all candidate users."""
        db = get_database()
        return list(db.users.find({'role': 'candidate'}))


class TestModel:
    """Test model for storing interview tests."""
    
    @staticmethod
    def create_test(title, description, prompt, created_by, total_questions=5):
        """Create a new test."""
        db = get_database()
        
        test = {
            'title': title,
            'description': description,
            'prompt': prompt,  # The prompt used to generate questions
            'created_by': ObjectId(created_by),
            'total_questions': total_questions,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = db.tests.insert_one(test)
        test['_id'] = result.inserted_id
        return test
    
    @staticmethod
    def find_by_id(test_id):
        """Find test by ID."""
        db = get_database()
        return db.tests.find_one({'_id': ObjectId(test_id)})
    
    @staticmethod
    def get_all_tests():
        """Get all tests."""
        db = get_database()
        return list(db.tests.find().sort('created_at', -1))
    
    @staticmethod
    def get_tests_by_admin(admin_id):
        """Get all tests created by an admin."""
        db = get_database()
        return list(db.tests.find({'created_by': ObjectId(admin_id)}).sort('created_at', -1))


class TestAssignmentModel:
    """Model for assigning tests to candidates."""
    
    @staticmethod
    def assign_test(test_id, candidate_id, assigned_by):
        """Assign a test to a candidate."""
        db = get_database()
        
        assignment = {
            'test_id': ObjectId(test_id),
            'candidate_id': ObjectId(candidate_id),
            'assigned_by': ObjectId(assigned_by),
            'status': 'pending',  # pending, in_progress, completed
            'assigned_at': datetime.utcnow()
        }
        
        try:
            result = db.test_assignments.insert_one(assignment)
            assignment['_id'] = result.inserted_id
            return assignment
        except Exception as e:
            logger.error(f"Error assigning test: {e}")
            return None
    
    @staticmethod
    def get_candidate_assignments(candidate_id):
        """Get all test assignments for a candidate."""
        db = get_database()
        return list(db.test_assignments.find({'candidate_id': ObjectId(candidate_id)}))
    
    @staticmethod
    def get_assignment(test_id, candidate_id):
        """Get specific assignment."""
        db = get_database()
        return db.test_assignments.find_one({
            'test_id': ObjectId(test_id),
            'candidate_id': ObjectId(candidate_id)
        })
    
    @staticmethod
    def update_status(assignment_id, status):
        """Update assignment status."""
        db = get_database()
        db.test_assignments.update_one(
            {'_id': ObjectId(assignment_id)},
            {'$set': {'status': status}}
        )
    
    @staticmethod
    def get_all_assignments():
        """Get all assignments."""
        db = get_database()
        return list(db.test_assignments.find().sort('assigned_at', -1))


class TestResultModel:
    """Model for storing test results."""
    
    @staticmethod
    def save_result(test_id, candidate_id, questions, answers, scores, total_score):
        """Save test result."""
        db = get_database()
        
        result = {
            'test_id': ObjectId(test_id),
            'candidate_id': ObjectId(candidate_id),
            'questions': questions,
            'answers': answers,
            'scores': scores,
            'total_score': total_score,
            'total_questions': len(questions),
            'percentage': (total_score / len(questions) * 100) if questions else 0,
            'completed_at': datetime.utcnow()
        }
        
        db_result = db.test_results.insert_one(result)
        result['_id'] = db_result.inserted_id
        return result
    
    @staticmethod
    def get_candidate_results(candidate_id):
        """Get all results for a candidate."""
        db = get_database()
        return list(db.test_results.find({'candidate_id': ObjectId(candidate_id)}).sort('completed_at', -1))
    
    @staticmethod
    def get_test_results(test_id):
        """Get all results for a specific test."""
        db = get_database()
        return list(db.test_results.find({'test_id': ObjectId(test_id)}).sort('completed_at', -1))
    
    @staticmethod
    def get_result_by_test_and_candidate(test_id, candidate_id):
        """Get result for a specific test and candidate."""
        db = get_database()
        return db.test_results.find_one({
            'test_id': ObjectId(test_id),
            'candidate_id': ObjectId(candidate_id)
        })
