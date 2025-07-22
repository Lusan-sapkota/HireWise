"""
Machine Learning services for job matching and scoring.
"""

import os
import json
import logging
import time
import pickle
import joblib
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import pandas as pd
import re

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


class MLModelError(Exception):
    """Custom exception for ML model errors"""
    pass


class JobMatchMLModel:
    """
    Machine Learning model for calculating job-resume match scores
    """
    
    def __init__(self):
        self.model_path = getattr(settings, 'ML_MODEL_PATH', 'matcher/models/job_matcher.pkl')
        self.vectorizer_path = getattr(settings, 'ML_VECTORIZER_PATH', 'matcher/models/tfidf_vectorizer.pkl')
        self.scaler_path = getattr(settings, 'ML_SCALER_PATH', 'matcher/models/feature_scaler.pkl')
        
        self.model = None
        self.vectorizer = None
        self.scaler = None
        self.is_initialized = False
        
        # Feature weights for scoring
        self.feature_weights = {
            'skill_match': 0.4,
            'experience_match': 0.25,
            'education_match': 0.15,
            'location_match': 0.1,
            'text_similarity': 0.1
        }
        
        self._initialize_model()
    
    def _initialize_model(self):
        """
        Initialize the ML model, vectorizer, and scaler
        """
        try:
            # Try to load existing model
            if self._load_existing_model():
                self.is_initialized = True
                logger.info("ML model loaded successfully")
                return
            
            # If no existing model, create and train a new one
            logger.info("No existing model found, creating new model")
            self._create_and_train_model()
            self.is_initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize ML model: {str(e)}")
            # Fall back to rule-based scoring
            self.is_initialized = False
    
    def _load_existing_model(self) -> bool:
        """
        Load existing trained model from disk
        """
        try:
            model_full_path = os.path.join(settings.BASE_DIR, self.model_path)
            vectorizer_full_path = os.path.join(settings.BASE_DIR, self.vectorizer_path)
            scaler_full_path = os.path.join(settings.BASE_DIR, self.scaler_path)
            
            if not all(os.path.exists(path) for path in [model_full_path, vectorizer_full_path, scaler_full_path]):
                return False
            
            self.model = joblib.load(model_full_path)
            self.vectorizer = joblib.load(vectorizer_full_path)
            self.scaler = joblib.load(scaler_full_path)
            
            logger.info("Loaded existing ML model components")
            return True
            
        except Exception as e:
            logger.error(f"Error loading existing model: {str(e)}")
            return False
    
    def _create_and_train_model(self):
        """
        Create and train a new ML model with synthetic data
        """
        try:
            # Create directories if they don't exist
            model_dir = os.path.dirname(os.path.join(settings.BASE_DIR, self.model_path))
            os.makedirs(model_dir, exist_ok=True)
            
            # Generate synthetic training data
            training_data = self._generate_synthetic_training_data()
            
            # Prepare features and targets
            X, y = self._prepare_training_data(training_data)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Train model
            self.model = RandomForestRegressor(n_estimators=100, random_state=42)
            self.model.fit(X_train, y_train)
            
            # Evaluate model
            y_pred = self.model.predict(X_test)
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            logger.info(f"Model trained - MSE: {mse:.4f}, R2: {r2:.4f}")
            
            # Save model components
            self._save_model_components()
            
        except Exception as e:
            logger.error(f"Error creating and training model: {str(e)}")
            raise MLModelError(f"Failed to create ML model: {str(e)}")
    
    def _generate_synthetic_training_data(self) -> List[Dict]:
        """
        Generate synthetic training data for the model
        """
        import random
        
        skills_pool = [
            'Python', 'JavaScript', 'Java', 'React', 'Django', 'Node.js', 'SQL', 'AWS',
            'Docker', 'Kubernetes', 'Machine Learning', 'Data Science', 'HTML', 'CSS',
            'Angular', 'Vue.js', 'MongoDB', 'PostgreSQL', 'Redis', 'Git', 'Linux',
            'C++', 'C#', '.NET', 'Spring Boot', 'Express.js', 'Flask', 'FastAPI'
        ]
        
        locations = ['Remote', 'New York', 'San Francisco', 'Seattle', 'Austin', 'Boston', 'Chicago']
        experience_levels = ['entry', 'mid', 'senior', 'lead']
        education_levels = ['Bachelor', 'Master', 'PhD', 'Associate', 'High School']
        
        training_data = []
        
        for _ in range(1000):  # Generate 1000 synthetic examples
            # Generate job requirements
            job_skills = random.sample(skills_pool, random.randint(3, 8))
            job_experience = random.choice(experience_levels)
            job_location = random.choice(locations)
            job_education = random.choice(education_levels)
            
            # Generate resume data
            resume_skills = random.sample(skills_pool, random.randint(2, 10))
            resume_experience = random.choice(experience_levels)
            resume_location = random.choice(locations)
            resume_education = random.choice(education_levels)
            
            # Calculate ground truth score based on matches
            skill_overlap = len(set(job_skills) & set(resume_skills)) / len(set(job_skills) | set(resume_skills))
            experience_match = 1.0 if job_experience == resume_experience else 0.5
            location_match = 1.0 if job_location == resume_location or job_location == 'Remote' else 0.3
            education_match = 1.0 if job_education == resume_education else 0.7
            
            # Calculate weighted score
            score = (
                skill_overlap * self.feature_weights['skill_match'] +
                experience_match * self.feature_weights['experience_match'] +
                location_match * self.feature_weights['location_match'] +
                education_match * self.feature_weights['education_match'] +
                random.uniform(0.5, 1.0) * self.feature_weights['text_similarity']
            )
            
            # Add some noise
            score += random.uniform(-0.1, 0.1)
            score = max(0, min(1, score))  # Clamp between 0 and 1
            
            training_data.append({
                'job_skills': job_skills,
                'job_experience': job_experience,
                'job_location': job_location,
                'job_education': job_education,
                'resume_skills': resume_skills,
                'resume_experience': resume_experience,
                'resume_location': resume_location,
                'resume_education': resume_education,
                'score': score
            })
        
        return training_data
    
    def _prepare_training_data(self, training_data: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare training data for the ML model
        """
        # Prepare text data for TF-IDF
        job_texts = []
        resume_texts = []
        
        for item in training_data:
            job_text = ' '.join(item['job_skills']) + ' ' + item['job_experience'] + ' ' + item['job_location']
            resume_text = ' '.join(item['resume_skills']) + ' ' + item['resume_experience'] + ' ' + item['resume_location']
            job_texts.append(job_text)
            resume_texts.append(resume_text)
        
        # Create and fit TF-IDF vectorizer
        all_texts = job_texts + resume_texts
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english', lowercase=True)
        self.vectorizer.fit(all_texts)
        
        # Prepare feature matrix
        features = []
        targets = []
        
        for i, item in enumerate(training_data):
            # Extract features
            feature_vector = self._extract_features(
                job_text=job_texts[i],
                resume_text=resume_texts[i],
                job_data={
                    'skills': item['job_skills'],
                    'experience_level': item['job_experience'],
                    'location': item['job_location'],
                    'education': item['job_education']
                },
                resume_data={
                    'skills': item['resume_skills'],
                    'experience_level': item['resume_experience'],
                    'location': item['resume_location'],
                    'education': item['resume_education']
                }
            )
            
            features.append(feature_vector)
            targets.append(item['score'])
        
        # Convert to numpy arrays
        X = np.array(features)
        y = np.array(targets)
        
        # Scale features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        return X_scaled, y
    
    def _extract_features(self, job_text: str, resume_text: str, job_data: Dict, resume_data: Dict) -> List[float]:
        """
        Extract features for the ML model
        """
        features = []
        
        # Text similarity features
        if self.vectorizer is not None:
            try:
                job_tfidf = self.vectorizer.transform([job_text])
                resume_tfidf = self.vectorizer.transform([resume_text])
                text_similarity = cosine_similarity(job_tfidf, resume_tfidf)[0][0]
                features.append(text_similarity)
            except Exception as e:
                logger.warning(f"Error calculating text similarity: {str(e)}")
                features.append(0.5)  # Default similarity
        else:
            # Use simple text similarity if vectorizer not available
            features.append(self._simple_text_similarity(job_text, resume_text))
        
        # Skill match features
        job_skills = set()
        if 'skills_required' in job_data:
            if isinstance(job_data['skills_required'], list):
                job_skills = set(skill.lower() for skill in job_data['skills_required'])
            elif isinstance(job_data['skills_required'], str):
                job_skills = set(skill.strip().lower() for skill in job_data['skills_required'].split(','))
        
        resume_skills = set()
        if 'skills' in resume_data:
            if isinstance(resume_data['skills'], list):
                resume_skills = set(skill.lower() for skill in resume_data['skills'])
            elif isinstance(resume_data['skills'], str):
                resume_skills = set(skill.strip().lower() for skill in resume_data['skills'].split(','))
        
        if job_skills and resume_skills:
            skill_intersection = len(job_skills & resume_skills)
            skill_union = len(job_skills | resume_skills)
            skill_jaccard = skill_intersection / skill_union if skill_union > 0 else 0
            skill_coverage = skill_intersection / len(job_skills) if job_skills else 0
        else:
            skill_jaccard = 0
            skill_coverage = 0
        
        features.extend([skill_jaccard, skill_coverage])
        
        # Experience match
        experience_levels = {'entry': 1, 'mid': 2, 'senior': 3, 'lead': 4}
        job_exp = experience_levels.get(job_data.get('experience_level', '').lower(), 2)
        resume_exp = experience_levels.get(resume_data.get('experience_level', '').lower(), 2)
        exp_diff = abs(job_exp - resume_exp) / 3.0  # Normalize by max difference
        features.append(1 - exp_diff)  # Higher score for smaller difference
        
        # Location match
        job_location = job_data.get('location', '').lower()
        resume_location = resume_data.get('location', '').lower()
        remote_allowed = job_data.get('remote_work_allowed', False)
        location_match = 1.0 if job_location == resume_location or 'remote' in job_location or remote_allowed else 0.3
        features.append(location_match)
        
        # Education match (simplified)
        education_levels = {'high school': 1, 'associate': 2, 'bachelor': 3, 'master': 4, 'phd': 5}
        job_edu = education_levels.get(job_data.get('education_required', '').lower(), 3)
        resume_edu = education_levels.get(resume_data.get('education', '').lower(), 3)
        edu_match = 1.0 if resume_edu >= job_edu else resume_edu / job_edu
        features.append(edu_match)
        
        # Ensure we always return a consistent number of features
        if len(features) != 6:
            logger.warning(f"Expected 6 features, got {len(features)}. Padding with defaults.")
            while len(features) < 6:
                features.append(0.5)
        
        return features
    
    def _save_model_components(self):
        """
        Save trained model components to disk
        """
        try:
            model_full_path = os.path.join(settings.BASE_DIR, self.model_path)
            vectorizer_full_path = os.path.join(settings.BASE_DIR, self.vectorizer_path)
            scaler_full_path = os.path.join(settings.BASE_DIR, self.scaler_path)
            
            joblib.dump(self.model, model_full_path)
            joblib.dump(self.vectorizer, vectorizer_full_path)
            joblib.dump(self.scaler, scaler_full_path)
            
            logger.info("ML model components saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving model components: {str(e)}")
            raise MLModelError(f"Failed to save model: {str(e)}")
    
    def calculate_match_score(self, resume_data: Dict, job_data: Dict) -> Dict[str, Any]:
        """
        Calculate match score between resume and job
        
        Args:
            resume_data: Dictionary containing resume information
            job_data: Dictionary containing job information
            
        Returns:
            Dictionary with match score and details
        """
        start_time = time.time()
        
        try:
            if self.is_initialized and self.model is not None:
                # Use ML model for scoring
                score_result = self._ml_based_scoring(resume_data, job_data)
            else:
                # Fall back to rule-based scoring
                logger.warning("ML model not available, using rule-based scoring")
                score_result = self._rule_based_scoring(resume_data, job_data)
            
            processing_time = time.time() - start_time
            score_result['processing_time'] = processing_time
            score_result['timestamp'] = time.time()
            
            return score_result
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error calculating match score: {str(e)}")
            
            return {
                'success': False,
                'error': str(e),
                'processing_time': processing_time,
                'timestamp': time.time()
            }
    
    def _ml_based_scoring(self, resume_data: Dict, job_data: Dict) -> Dict[str, Any]:
        """
        Calculate match score using ML model
        """
        try:
            # Prepare text data
            job_text = self._prepare_job_text(job_data)
            resume_text = self._prepare_resume_text(resume_data)
            
            # Extract features
            feature_vector = self._extract_features(job_text, resume_text, job_data, resume_data)
            
            # Scale features
            feature_vector_scaled = self.scaler.transform([feature_vector])
            
            # Predict score
            predicted_score = self.model.predict(feature_vector_scaled)[0]
            
            # Ensure score is between 0 and 1
            predicted_score = max(0, min(1, predicted_score))
            
            # Convert to 0-100 scale
            match_score = predicted_score * 100
            
            # Get detailed analysis
            analysis = self._analyze_match_details(resume_data, job_data)
            
            return {
                'success': True,
                'match_score': round(match_score, 2),
                'confidence': 0.85,  # ML model confidence
                'method': 'ml_model',
                'analysis': analysis
            }
            
        except Exception as e:
            logger.error(f"Error in ML-based scoring: {str(e)}")
            raise MLModelError(f"ML scoring failed: {str(e)}")
    
    def _rule_based_scoring(self, resume_data: Dict, job_data: Dict) -> Dict[str, Any]:
        """
        Calculate match score using rule-based approach (fallback)
        """
        try:
            scores = {}
            
            # Skill matching
            scores['skill_match'] = self._calculate_skill_match(resume_data, job_data)
            
            # Experience matching
            scores['experience_match'] = self._calculate_experience_match(resume_data, job_data)
            
            # Location matching
            scores['location_match'] = self._calculate_location_match(resume_data, job_data)
            
            # Education matching
            scores['education_match'] = self._calculate_education_match(resume_data, job_data)
            
            # Text similarity
            scores['text_similarity'] = self._calculate_text_similarity(resume_data, job_data)
            
            # Calculate weighted final score
            final_score = sum(
                scores[key] * self.feature_weights[key] 
                for key in scores.keys() 
                if key in self.feature_weights
            )
            
            # Convert to 0-100 scale
            match_score = final_score * 100
            
            # Get detailed analysis
            analysis = self._analyze_match_details(resume_data, job_data)
            analysis['component_scores'] = scores
            
            return {
                'success': True,
                'match_score': round(match_score, 2),
                'confidence': 0.75,  # Rule-based confidence
                'method': 'rule_based',
                'analysis': analysis
            }
            
        except Exception as e:
            logger.error(f"Error in rule-based scoring: {str(e)}")
            raise MLModelError(f"Rule-based scoring failed: {str(e)}")
    
    def _prepare_job_text(self, job_data: Dict) -> str:
        """
        Prepare job text for analysis
        """
        text_parts = []
        
        if 'title' in job_data:
            text_parts.append(job_data['title'])
        if 'description' in job_data:
            text_parts.append(job_data['description'])
        if 'requirements' in job_data:
            text_parts.append(job_data['requirements'])
        if 'skills_required' in job_data:
            if isinstance(job_data['skills_required'], list):
                text_parts.extend(job_data['skills_required'])
            else:
                text_parts.append(job_data['skills_required'])
        
        return ' '.join(text_parts)
    
    def _prepare_resume_text(self, resume_data: Dict) -> str:
        """
        Prepare resume text for analysis
        """
        text_parts = []
        
        if 'parsed_text' in resume_data:
            text_parts.append(resume_data['parsed_text'])
        if 'skills' in resume_data:
            if isinstance(resume_data['skills'], list):
                text_parts.extend(resume_data['skills'])
            else:
                text_parts.append(resume_data['skills'])
        
        return ' '.join(text_parts)
    
    def _calculate_skill_match(self, resume_data: Dict, job_data: Dict) -> float:
        """
        Calculate skill matching score
        """
        # Extract skills from job
        job_skills = set()
        if 'skills_required' in job_data:
            if isinstance(job_data['skills_required'], str):
                job_skills.update(skill.strip().lower() for skill in job_data['skills_required'].split(','))
            elif isinstance(job_data['skills_required'], list):
                job_skills.update(skill.lower() for skill in job_data['skills_required'])
        
        # Extract skills from resume
        resume_skills = set()
        if 'skills' in resume_data:
            if isinstance(resume_data['skills'], str):
                resume_skills.update(skill.strip().lower() for skill in resume_data['skills'].split(','))
            elif isinstance(resume_data['skills'], list):
                resume_skills.update(skill.lower() for skill in resume_data['skills'])
        
        # Also extract from parsed text
        if 'parsed_text' in resume_data:
            resume_skills.update(self._extract_skills_from_text(resume_data['parsed_text']))
        
        if not job_skills:
            return 0.5  # Neutral score if no job skills specified
        
        # Calculate Jaccard similarity
        intersection = len(job_skills & resume_skills)
        union = len(job_skills | resume_skills)
        
        return intersection / union if union > 0 else 0
    
    def _calculate_experience_match(self, resume_data: Dict, job_data: Dict) -> float:
        """
        Calculate experience level matching score
        """
        experience_levels = {'entry': 1, 'mid': 2, 'senior': 3, 'lead': 4, 'executive': 5}
        
        job_exp = experience_levels.get(job_data.get('experience_level', '').lower(), 2)
        resume_exp = experience_levels.get(resume_data.get('experience_level', '').lower(), 2)
        
        # Also consider years of experience if available
        if 'total_experience_years' in resume_data:
            years = resume_data['total_experience_years']
            if years <= 2:
                resume_exp = max(resume_exp, 1)
            elif years <= 5:
                resume_exp = max(resume_exp, 2)
            elif years <= 10:
                resume_exp = max(resume_exp, 3)
            else:
                resume_exp = max(resume_exp, 4)
        
        # Calculate match score
        if resume_exp >= job_exp:
            return 1.0  # Perfect match or overqualified
        else:
            return resume_exp / job_exp  # Underqualified
    
    def _calculate_location_match(self, resume_data: Dict, job_data: Dict) -> float:
        """
        Calculate location matching score
        """
        job_location = job_data.get('location', '').lower()
        resume_location = resume_data.get('location', '').lower()
        
        # Remote work gets high score
        if 'remote' in job_location or job_data.get('remote_work_allowed', False):
            return 1.0
        
        # Exact location match
        if job_location == resume_location:
            return 1.0
        
        # Partial location match (same city/state)
        if job_location and resume_location:
            job_parts = set(job_location.split())
            resume_parts = set(resume_location.split())
            if job_parts & resume_parts:
                return 0.7
        
        return 0.3  # Default for different locations
    
    def _calculate_education_match(self, resume_data: Dict, job_data: Dict) -> float:
        """
        Calculate education matching score
        """
        education_levels = {
            'high school': 1, 'associate': 2, 'bachelor': 3, 
            'master': 4, 'phd': 5, 'doctorate': 5
        }
        
        job_edu = job_data.get('education_required', '').lower()
        resume_edu = resume_data.get('education', '').lower()
        
        # If no education requirement specified, give neutral score
        if not job_edu:
            return 0.8
        
        job_level = 3  # Default to bachelor's
        for edu, level in education_levels.items():
            if edu in job_edu:
                job_level = level
                break
        
        resume_level = 3  # Default to bachelor's
        for edu, level in education_levels.items():
            if edu in resume_edu:
                resume_level = level
                break
        
        # Calculate match score
        if resume_level >= job_level:
            return 1.0
        else:
            return resume_level / job_level
    
    def _calculate_text_similarity(self, resume_data: Dict, job_data: Dict) -> float:
        """
        Calculate text similarity between resume and job description
        """
        try:
            job_text = self._prepare_job_text(job_data)
            resume_text = self._prepare_resume_text(resume_data)
            
            if not job_text or not resume_text:
                return 0.5
            
            # Use simple TF-IDF if vectorizer not available
            if self.vectorizer is None:
                return self._simple_text_similarity(job_text, resume_text)
            
            # Use trained vectorizer
            job_tfidf = self.vectorizer.transform([job_text])
            resume_tfidf = self.vectorizer.transform([resume_text])
            
            similarity = cosine_similarity(job_tfidf, resume_tfidf)[0][0]
            return similarity
            
        except Exception as e:
            logger.error(f"Error calculating text similarity: {str(e)}")
            return 0.5
    
    def _simple_text_similarity(self, text1: str, text2: str) -> float:
        """
        Simple text similarity calculation without TF-IDF
        """
        # Convert to lowercase and split into words
        words1 = set(re.findall(r'\w+', text1.lower()))
        words2 = set(re.findall(r'\w+', text2.lower()))
        
        # Calculate Jaccard similarity
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0
    
    def _extract_skills_from_text(self, text: str) -> set:
        """
        Extract skills from text using simple pattern matching
        """
        # Common technical skills patterns
        skill_patterns = [
            r'\b(?:python|java|javascript|react|angular|vue|django|flask|spring|node\.?js)\b',
            r'\b(?:sql|mysql|postgresql|mongodb|redis|elasticsearch)\b',
            r'\b(?:aws|azure|gcp|docker|kubernetes|jenkins|git)\b',
            r'\b(?:html|css|bootstrap|tailwind|sass|less)\b',
            r'\b(?:machine learning|data science|ai|ml|deep learning)\b'
        ]
        
        skills = set()
        text_lower = text.lower()
        
        for pattern in skill_patterns:
            matches = re.findall(pattern, text_lower)
            skills.update(matches)
        
        return skills
    
    def _analyze_match_details(self, resume_data: Dict, job_data: Dict) -> Dict[str, Any]:
        """
        Provide detailed analysis of the match
        """
        analysis = {
            'matching_skills': [],
            'missing_skills': [],
            'experience_analysis': '',
            'location_analysis': '',
            'recommendations': []
        }
        
        # Skill analysis
        job_skills = set()
        if 'skills_required' in job_data:
            if isinstance(job_data['skills_required'], str):
                job_skills.update(skill.strip().lower() for skill in job_data['skills_required'].split(','))
            elif isinstance(job_data['skills_required'], list):
                job_skills.update(skill.lower() for skill in job_data['skills_required'])
        
        resume_skills = set()
        if 'skills' in resume_data:
            if isinstance(resume_data['skills'], str):
                resume_skills.update(skill.strip().lower() for skill in resume_data['skills'].split(','))
            elif isinstance(resume_data['skills'], list):
                resume_skills.update(skill.lower() for skill in resume_data['skills'])
        
        analysis['matching_skills'] = list(job_skills & resume_skills)
        analysis['missing_skills'] = list(job_skills - resume_skills)
        
        # Experience analysis
        job_exp = job_data.get('experience_level', '')
        resume_exp = resume_data.get('experience_level', '')
        
        if job_exp and resume_exp:
            if job_exp.lower() == resume_exp.lower():
                analysis['experience_analysis'] = f"Perfect match for {job_exp} level position"
            else:
                analysis['experience_analysis'] = f"Job requires {job_exp}, candidate has {resume_exp} experience"
        
        # Location analysis
        job_location = job_data.get('location', '')
        resume_location = resume_data.get('location', '')
        
        if 'remote' in job_location.lower() or job_data.get('remote_work_allowed', False):
            analysis['location_analysis'] = "Remote work available - location flexible"
        elif job_location.lower() == resume_location.lower():
            analysis['location_analysis'] = f"Perfect location match in {job_location}"
        else:
            analysis['location_analysis'] = f"Job in {job_location}, candidate in {resume_location}"
        
        # Recommendations
        if analysis['missing_skills']:
            analysis['recommendations'].append(f"Consider developing skills in: {', '.join(analysis['missing_skills'][:3])}")
        
        if len(analysis['matching_skills']) > 0:
            analysis['recommendations'].append(f"Strong match in: {', '.join(analysis['matching_skills'][:3])}")
        
        return analysis


# Global model instance
_ml_model_instance = None

def get_ml_model() -> JobMatchMLModel:
    """
    Get singleton instance of the ML model
    """
    global _ml_model_instance
    if _ml_model_instance is None:
        _ml_model_instance = JobMatchMLModel()
    return _ml_model_instance


class FeatureExtractor:
    """
    Utility class for extracting features from resume and job data
    """
    
    @staticmethod
    def extract_resume_features(resume_data: Dict) -> Dict[str, Any]:
        """
        Extract standardized features from resume data
        """
        features = {
            'skills': [],
            'experience_level': 'mid',
            'total_experience_years': 0,
            'education': 'bachelor',
            'location': '',
            'parsed_text': ''
        }
        
        # Extract from structured data if available
        if 'structured_data' in resume_data and resume_data['structured_data']:
            structured = resume_data['structured_data']
            
            # Skills
            if 'skills' in structured:
                skills_data = structured['skills']
                all_skills = []
                for skill_type in ['technical_skills', 'programming_languages', 'frameworks', 'tools']:
                    if skill_type in skills_data and isinstance(skills_data[skill_type], list):
                        all_skills.extend(skills_data[skill_type])
                features['skills'] = all_skills
            
            # Experience
            if 'total_experience_years' in structured:
                features['total_experience_years'] = structured['total_experience_years']
            
            # Education
            if 'education' in structured and structured['education']:
                education_list = structured['education']
                if education_list and isinstance(education_list, list):
                    # Get highest education level
                    highest_edu = education_list[0].get('degree', '')
                    features['education'] = highest_edu
            
            # Location
            if 'personal_info' in structured and 'location' in structured['personal_info']:
                features['location'] = structured['personal_info']['location'] or ''
        
        # Extract from direct fields
        if 'parsed_text' in resume_data:
            features['parsed_text'] = resume_data['parsed_text']
        
        if 'skills' in resume_data and not features['skills']:
            if isinstance(resume_data['skills'], str):
                features['skills'] = [s.strip() for s in resume_data['skills'].split(',')]
            elif isinstance(resume_data['skills'], list):
                features['skills'] = resume_data['skills']
        
        return features
    
    @staticmethod
    def extract_job_features(job_data: Dict) -> Dict[str, Any]:
        """
        Extract standardized features from job data
        """
        features = {
            'title': job_data.get('title', ''),
            'description': job_data.get('description', ''),
            'requirements': job_data.get('requirements', ''),
            'skills_required': [],
            'experience_level': job_data.get('experience_level', 'mid'),
            'location': job_data.get('location', ''),
            'remote_work_allowed': job_data.get('remote_work_allowed', False),
            'education_required': job_data.get('education_required', ''),
            'salary_min': job_data.get('salary_min'),
            'salary_max': job_data.get('salary_max')
        }
        
        # Parse skills
        if 'skills_required' in job_data:
            skills = job_data['skills_required']
            if isinstance(skills, str):
                features['skills_required'] = [s.strip() for s in skills.split(',')]
            elif isinstance(skills, list):
                features['skills_required'] = skills
        
        return features


class MatchScoreCache:
    """
    Caching utility for match scores
    """
    
    CACHE_TIMEOUT = 3600  # 1 hour
    
    @staticmethod
    def get_cache_key(resume_id: str, job_id: str) -> str:
        """
        Generate cache key for match score
        """
        return f"match_score:{resume_id}:{job_id}"
    
    @staticmethod
    def get_cached_score(resume_id: str, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached match score
        """
        cache_key = MatchScoreCache.get_cache_key(resume_id, job_id)
        return cache.get(cache_key)
    
    @staticmethod
    def cache_score(resume_id: str, job_id: str, score_data: Dict[str, Any]):
        """
        Cache match score
        """
        cache_key = MatchScoreCache.get_cache_key(resume_id, job_id)
        cache.set(cache_key, score_data, MatchScoreCache.CACHE_TIMEOUT)
    
    @staticmethod
    def invalidate_cache(resume_id: str = None, job_id: str = None):
        """
        Invalidate cached scores
        """
        if resume_id and job_id:
            # Invalidate specific cache entry
            cache_key = MatchScoreCache.get_cache_key(resume_id, job_id)
            cache.delete(cache_key)
        else:
            # This would require a more sophisticated cache invalidation strategy
            # For now, we'll rely on cache timeout
            pass