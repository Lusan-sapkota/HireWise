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
from django.db import models

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


# =============================================================================
# AI INTERVIEW SERVICES
# =============================================================================

import google.generativeai as genai
from django.conf import settings

# Configure Gemini API
if hasattr(settings, 'GEMINI_API_KEY') and settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)


class AIInterviewService:
    """
    Service for AI-powered interview functionality using Google Gemini
    """
    
    def __init__(self):
        self.model_name = getattr(settings, 'GEMINI_MODEL_NAME', 'gemini-pro')
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the Gemini model"""
        try:
            if hasattr(settings, 'GEMINI_API_KEY') and settings.GEMINI_API_KEY:
                self.model = genai.GenerativeModel(self.model_name)
                logger.info("Gemini AI model initialized successfully")
            else:
                logger.warning("Gemini API key not configured")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {str(e)}")
            self.model = None
    
    def generate_questions(self, job_post, resume, interview_type='technical', num_questions=5):
        """
        Generate interview questions based on job requirements and candidate resume
        
        Args:
            job_post: JobPost instance
            resume: Resume instance
            interview_type: Type of interview ('technical', 'behavioral', 'situational')
            num_questions: Number of questions to generate
            
        Returns:
            List of generated questions with metadata
        """
        try:
            if not self.model:
                return self._fallback_questions(interview_type, num_questions)
            
            # Prepare context for AI
            job_context = self._prepare_job_context(job_post)
            resume_context = self._prepare_resume_context(resume)
            
            # Create prompt based on interview type
            prompt = self._create_question_generation_prompt(
                job_context, resume_context, interview_type, num_questions
            )
            
            # Generate questions using Gemini
            response = self.model.generate_content(prompt)
            questions = self._parse_generated_questions(response.text, interview_type)
            
            logger.info(f"Generated {len(questions)} {interview_type} interview questions")
            return questions
            
        except Exception as e:
            logger.error(f"Error generating interview questions: {str(e)}")
            return self._fallback_questions(interview_type, num_questions)
    
    def analyze_response(self, question, response, job_context=None):
        """
        Analyze a candidate's response to an interview question
        
        Args:
            question: The interview question
            response: Candidate's response
            job_context: Additional job context for analysis
            
        Returns:
            Analysis results with score and feedback
        """
        try:
            if not self.model:
                return self._fallback_analysis(response)
            
            # Create analysis prompt
            prompt = self._create_response_analysis_prompt(question, response, job_context)
            
            # Analyze response using Gemini
            response_obj = self.model.generate_content(prompt)
            analysis = self._parse_response_analysis(response_obj.text)
            
            logger.info(f"Analyzed interview response with score: {analysis.get('score', 'N/A')}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing interview response: {str(e)}")
            return self._fallback_analysis(response)
    
    def generate_session_analysis(self, session):
        """
        Generate comprehensive analysis for completed interview session
        
        Args:
            session: InterviewSession instance
            
        Returns:
            Comprehensive session analysis
        """
        try:
            if not self.model:
                return self._fallback_session_analysis(session)
            
            # Get all questions and responses for the session
            questions_data = self._get_session_questions_data(session)
            
            if not questions_data:
                return self._fallback_session_analysis(session)
            
            # Create comprehensive analysis prompt
            prompt = self._create_session_analysis_prompt(session, questions_data)
            
            # Generate analysis using Gemini
            response = self.model.generate_content(prompt)
            analysis = self._parse_session_analysis(response.text)
            
            logger.info(f"Generated comprehensive analysis for session {session.id}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error generating session analysis: {str(e)}")
            return self._fallback_session_analysis(session)
    
    def _prepare_job_context(self, job_post):
        """Prepare job context for AI prompts"""
        return {
            'title': job_post.title,
            'description': job_post.description,
            'requirements': job_post.requirements,
            'skills_required': job_post.skills_required,
            'experience_level': job_post.experience_level,
            'job_type': job_post.job_type,
            'location': job_post.location
        }
    
    def _prepare_resume_context(self, resume):
        """Prepare resume context for AI prompts"""
        context = {
            'parsed_text': resume.parsed_text or '',
            'filename': resume.original_filename
        }
        
        # Add job seeker profile information if available
        if hasattr(resume.job_seeker, 'job_seeker_profile'):
            profile = resume.job_seeker.job_seeker_profile
            context.update({
                'experience_level': profile.experience_level,
                'current_position': profile.current_position,
                'skills': profile.skills,
                'location': profile.location
            })
        
        return context
    
    def _create_question_generation_prompt(self, job_context, resume_context, interview_type, num_questions):
        """Create prompt for question generation"""
        base_prompt = f"""
You are an expert technical interviewer. Generate {num_questions} {interview_type} interview questions for the following job position and candidate.

JOB DETAILS:
- Title: {job_context['title']}
- Description: {job_context['description'][:500]}...
- Requirements: {job_context['requirements'][:500]}...
- Required Skills: {job_context['skills_required']}
- Experience Level: {job_context['experience_level']}

CANDIDATE BACKGROUND:
- Experience Level: {resume_context.get('experience_level', 'Not specified')}
- Current Position: {resume_context.get('current_position', 'Not specified')}
- Skills: {resume_context.get('skills', 'Not specified')}
- Resume Summary: {resume_context['parsed_text'][:800]}...

Please generate {num_questions} {interview_type} questions that are:
1. Relevant to the job requirements
2. Appropriate for the candidate's experience level
3. Designed to assess key competencies for this role

Format each question as:
QUESTION [number]: [question text]
DIFFICULTY: [Easy/Medium/Hard]
FOCUS_AREA: [specific skill or competency being assessed]
EXPECTED_DURATION: [estimated time in minutes]

"""
        
        if interview_type == 'technical':
            base_prompt += """
Focus on technical skills, problem-solving abilities, and hands-on experience with the required technologies.
"""
        elif interview_type == 'behavioral':
            base_prompt += """
Focus on past experiences, leadership, teamwork, conflict resolution, and cultural fit.
"""
        elif interview_type == 'situational':
            base_prompt += """
Focus on hypothetical scenarios, decision-making processes, and how they would handle specific work situations.
"""
        
        return base_prompt
    
    def _create_response_analysis_prompt(self, question, response, job_context):
        """Create prompt for response analysis"""
        return f"""
You are an expert interview evaluator. Analyze the following candidate response to an interview question.

QUESTION: {question}

CANDIDATE RESPONSE: {response}

JOB CONTEXT: {job_context or 'General position'}

Please provide a comprehensive analysis including:

1. SCORE (0-100): Overall quality of the response
2. STRENGTHS: What the candidate did well
3. WEAKNESSES: Areas for improvement
4. TECHNICAL_ACCURACY: How technically sound is the response (if applicable)
5. COMMUNICATION: Clarity and structure of the response
6. RELEVANCE: How well the response addresses the question
7. DEPTH: Level of detail and insight provided
8. RECOMMENDATIONS: Specific suggestions for improvement

Format your response as:
SCORE: [0-100]
STRENGTHS: [bullet points]
WEAKNESSES: [bullet points]
TECHNICAL_ACCURACY: [assessment]
COMMUNICATION: [assessment]
RELEVANCE: [assessment]
DEPTH: [assessment]
RECOMMENDATIONS: [bullet points]
"""
    
    def _create_session_analysis_prompt(self, session, questions_data):
        """Create prompt for comprehensive session analysis"""
        questions_summary = "\n".join([
            f"Q{i+1}: {q['question']} (Score: {q.get('score', 'N/A')})"
            for i, q in enumerate(questions_data)
        ])
        
        return f"""
You are an expert interview evaluator. Provide a comprehensive analysis of this completed interview session.

INTERVIEW TYPE: {session.interview_type}
TOTAL QUESTIONS: {len(questions_data)}
DURATION: {session.duration_minutes} minutes

QUESTIONS AND PERFORMANCE:
{questions_summary}

JOB POSITION: {session.application.job_post.title}
COMPANY: {session.application.job_post.recruiter.recruiter_profile.company_name}

Please provide a comprehensive analysis including:

1. OVERALL_SCORE (0-100): Weighted average performance
2. PERFORMANCE_SUMMARY: Brief overview of candidate's performance
3. STRENGTHS: Key strengths demonstrated
4. AREAS_FOR_IMPROVEMENT: Specific areas needing development
5. TECHNICAL_COMPETENCY: Assessment of technical skills (if applicable)
6. COMMUNICATION_SKILLS: Evaluation of communication effectiveness
7. PROBLEM_SOLVING: Assessment of analytical and problem-solving abilities
8. CULTURAL_FIT: Likelihood of fitting well with the role and company
9. HIRING_RECOMMENDATION: Strong recommendation, conditional recommendation, or not recommended
10. DETAILED_FEEDBACK: Specific feedback for each major area
11. NEXT_STEPS: Suggested next steps in the hiring process

Format your response clearly with each section labeled.
"""
    
    def _parse_generated_questions(self, response_text, interview_type):
        """Parse AI-generated questions into structured format"""
        questions = []
        lines = response_text.strip().split('\n')
        
        current_question = {}
        
        for line in lines:
            line = line.strip()
            if line.startswith('QUESTION'):
                if current_question:
                    questions.append(current_question)
                current_question = {
                    'question_text': line.split(':', 1)[1].strip() if ':' in line else line,
                    'question_type': interview_type,
                    'difficulty_level': 'medium',
                    'expected_answer': '',
                    'focus_area': '',
                    'estimated_duration': 5
                }
            elif line.startswith('DIFFICULTY:'):
                current_question['difficulty_level'] = line.split(':', 1)[1].strip().lower()
            elif line.startswith('FOCUS_AREA:'):
                current_question['focus_area'] = line.split(':', 1)[1].strip()
            elif line.startswith('EXPECTED_DURATION:'):
                try:
                    duration = int(line.split(':', 1)[1].strip().split()[0])
                    current_question['estimated_duration'] = duration
                except (ValueError, IndexError):
                    current_question['estimated_duration'] = 5
        
        if current_question:
            questions.append(current_question)
        
        # Ensure we have at least some questions
        if not questions:
            questions = self._fallback_questions(interview_type, 3)
        
        return questions
    
    def _parse_response_analysis(self, response_text):
        """Parse AI response analysis into structured format"""
        analysis = {
            'score': 70,
            'strengths': [],
            'weaknesses': [],
            'technical_accuracy': 'Good',
            'communication': 'Clear',
            'relevance': 'Relevant',
            'depth': 'Adequate',
            'recommendations': [],
            'detailed_feedback': response_text
        }
        
        lines = response_text.strip().split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('SCORE:'):
                try:
                    score = int(line.split(':', 1)[1].strip())
                    analysis['score'] = max(0, min(100, score))
                except (ValueError, IndexError):
                    pass
            elif line.startswith('STRENGTHS:'):
                current_section = 'strengths'
                content = line.split(':', 1)[1].strip()
                if content:
                    analysis['strengths'].append(content)
            elif line.startswith('WEAKNESSES:'):
                current_section = 'weaknesses'
                content = line.split(':', 1)[1].strip()
                if content:
                    analysis['weaknesses'].append(content)
            elif line.startswith('TECHNICAL_ACCURACY:'):
                analysis['technical_accuracy'] = line.split(':', 1)[1].strip()
                current_section = None
            elif line.startswith('COMMUNICATION:'):
                analysis['communication'] = line.split(':', 1)[1].strip()
                current_section = None
            elif line.startswith('RELEVANCE:'):
                analysis['relevance'] = line.split(':', 1)[1].strip()
                current_section = None
            elif line.startswith('DEPTH:'):
                analysis['depth'] = line.split(':', 1)[1].strip()
                current_section = None
            elif line.startswith('RECOMMENDATIONS:'):
                current_section = 'recommendations'
                content = line.split(':', 1)[1].strip()
                if content:
                    analysis['recommendations'].append(content)
            elif line.startswith('- ') or line.startswith('• '):
                if current_section and current_section in analysis:
                    analysis[current_section].append(line[2:].strip())
        
        return analysis
    
    def _parse_session_analysis(self, response_text):
        """Parse comprehensive session analysis"""
        analysis = {
            'overall_score': 70,
            'performance_summary': 'Average performance',
            'strengths': [],
            'areas_for_improvement': [],
            'technical_competency': 'Adequate',
            'communication_skills': 'Good',
            'problem_solving': 'Satisfactory',
            'cultural_fit': 'Good fit',
            'hiring_recommendation': 'Conditional recommendation',
            'detailed_feedback': response_text,
            'next_steps': []
        }
        
        lines = response_text.strip().split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('OVERALL_SCORE'):
                try:
                    score = int(line.split(':', 1)[1].strip().split()[0])
                    analysis['overall_score'] = max(0, min(100, score))
                except (ValueError, IndexError):
                    pass
            elif line.startswith('PERFORMANCE_SUMMARY:'):
                analysis['performance_summary'] = line.split(':', 1)[1].strip()
            elif line.startswith('STRENGTHS:'):
                current_section = 'strengths'
                content = line.split(':', 1)[1].strip()
                if content:
                    analysis['strengths'].append(content)
            elif line.startswith('AREAS_FOR_IMPROVEMENT:'):
                current_section = 'areas_for_improvement'
                content = line.split(':', 1)[1].strip()
                if content:
                    analysis['areas_for_improvement'].append(content)
            elif line.startswith('TECHNICAL_COMPETENCY:'):
                analysis['technical_competency'] = line.split(':', 1)[1].strip()
                current_section = None
            elif line.startswith('COMMUNICATION_SKILLS:'):
                analysis['communication_skills'] = line.split(':', 1)[1].strip()
                current_section = None
            elif line.startswith('PROBLEM_SOLVING:'):
                analysis['problem_solving'] = line.split(':', 1)[1].strip()
                current_section = None
            elif line.startswith('CULTURAL_FIT:'):
                analysis['cultural_fit'] = line.split(':', 1)[1].strip()
                current_section = None
            elif line.startswith('HIRING_RECOMMENDATION:'):
                analysis['hiring_recommendation'] = line.split(':', 1)[1].strip()
                current_section = None
            elif line.startswith('NEXT_STEPS:'):
                current_section = 'next_steps'
                content = line.split(':', 1)[1].strip()
                if content:
                    analysis['next_steps'].append(content)
            elif line.startswith('- ') or line.startswith('• '):
                if current_section and current_section in analysis and isinstance(analysis[current_section], list):
                    analysis[current_section].append(line[2:].strip())
        
        return analysis
    
    def _get_session_questions_data(self, session):
        """Get all questions and responses for a session"""
        from .models import AIInterviewQuestion
        
        questions = AIInterviewQuestion.objects.filter(interview_session=session)
        questions_data = []
        
        for question in questions:
            questions_data.append({
                'question': question.question_text,
                'response': question.candidate_answer,
                'score': question.ai_score,
                'question_type': question.question_type,
                'difficulty': question.difficulty_level,
                'time_taken': question.time_taken_seconds
            })
        
        return questions_data
    
    def _fallback_questions(self, interview_type, num_questions):
        """Fallback questions when AI is not available"""
        fallback_questions = {
            'technical': [
                {
                    'question_text': 'Describe your experience with the main technologies mentioned in the job requirements.',
                    'question_type': 'technical',
                    'difficulty_level': 'medium',
                    'expected_answer': '',
                    'focus_area': 'Technical Experience',
                    'estimated_duration': 5
                },
                {
                    'question_text': 'Walk me through how you would approach solving a complex technical problem.',
                    'question_type': 'technical',
                    'difficulty_level': 'medium',
                    'expected_answer': '',
                    'focus_area': 'Problem Solving',
                    'estimated_duration': 7
                },
                {
                    'question_text': 'Describe a challenging project you worked on and how you overcame technical obstacles.',
                    'question_type': 'technical',
                    'difficulty_level': 'medium',
                    'expected_answer': '',
                    'focus_area': 'Project Experience',
                    'estimated_duration': 8
                }
            ],
            'behavioral': [
                {
                    'question_text': 'Tell me about a time when you had to work with a difficult team member.',
                    'question_type': 'behavioral',
                    'difficulty_level': 'medium',
                    'expected_answer': '',
                    'focus_area': 'Teamwork',
                    'estimated_duration': 6
                },
                {
                    'question_text': 'Describe a situation where you had to meet a tight deadline.',
                    'question_type': 'behavioral',
                    'difficulty_level': 'medium',
                    'expected_answer': '',
                    'focus_area': 'Time Management',
                    'estimated_duration': 5
                },
                {
                    'question_text': 'Give me an example of when you had to learn something new quickly.',
                    'question_type': 'behavioral',
                    'difficulty_level': 'medium',
                    'expected_answer': '',
                    'focus_area': 'Learning Ability',
                    'estimated_duration': 6
                }
            ],
            'situational': [
                {
                    'question_text': 'How would you handle a situation where you disagree with your manager\'s technical decision?',
                    'question_type': 'situational',
                    'difficulty_level': 'medium',
                    'expected_answer': '',
                    'focus_area': 'Conflict Resolution',
                    'estimated_duration': 6
                },
                {
                    'question_text': 'What would you do if you discovered a critical bug in production just before a major release?',
                    'question_type': 'situational',
                    'difficulty_level': 'hard',
                    'expected_answer': '',
                    'focus_area': 'Crisis Management',
                    'estimated_duration': 7
                },
                {
                    'question_text': 'How would you approach mentoring a junior developer who is struggling?',
                    'question_type': 'situational',
                    'difficulty_level': 'medium',
                    'expected_answer': '',
                    'focus_area': 'Leadership',
                    'estimated_duration': 6
                }
            ]
        }
        
        questions = fallback_questions.get(interview_type, fallback_questions['technical'])
        return questions[:num_questions]
    
    def _fallback_analysis(self, response):
        """Fallback analysis when AI is not available"""
        word_count = len(response.split())
        
        # Simple scoring based on response length and basic criteria
        if word_count < 20:
            score = 40
            feedback = "Response is too brief. Consider providing more detailed examples and explanations."
        elif word_count < 50:
            score = 60
            feedback = "Good start, but could benefit from more specific examples and details."
        elif word_count < 100:
            score = 75
            feedback = "Well-structured response with good detail. Consider adding specific metrics or outcomes."
        else:
            score = 85
            feedback = "Comprehensive response with good detail and structure."
        
        return {
            'score': score,
            'strengths': ['Provided a response', 'Addressed the question'],
            'weaknesses': ['Could provide more specific examples'],
            'technical_accuracy': 'Unable to assess without AI',
            'communication': 'Clear' if word_count > 30 else 'Brief',
            'relevance': 'Relevant',
            'depth': 'Adequate' if word_count > 50 else 'Limited',
            'recommendations': [feedback],
            'detailed_feedback': f"Response analysis (fallback mode): {feedback}"
        }
    
    def _fallback_session_analysis(self, session):
        """Fallback session analysis when AI is not available"""
        from .models import AIInterviewQuestion
        
        questions_count = AIInterviewQuestion.objects.filter(interview_session=session).count()
        avg_score = AIInterviewQuestion.objects.filter(interview_session=session).aggregate(
            avg_score=models.Avg('ai_score')
        )['avg_score'] or 70
        
        return {
            'overall_score': int(avg_score),
            'performance_summary': f'Completed {questions_count} questions with average performance',
            'strengths': ['Completed the interview', 'Provided responses to all questions'],
            'areas_for_improvement': ['Detailed analysis requires AI service'],
            'technical_competency': 'Requires AI analysis',
            'communication_skills': 'Requires AI analysis',
            'problem_solving': 'Requires AI analysis',
            'cultural_fit': 'Requires further evaluation',
            'hiring_recommendation': 'Requires detailed review',
            'detailed_feedback': 'Comprehensive analysis requires AI service to be available.',
            'next_steps': ['Schedule follow-up interview', 'Review with hiring manager']
        }


# Initialize AI Interview Service
ai_interview_service = AIInterviewService()


def generate_interview_questions(job_post, resume, interview_type='technical', num_questions=5):
    """
    Generate interview questions using AI service
    
    Args:
        job_post: JobPost instance
        resume: Resume instance  
        interview_type: Type of interview
        num_questions: Number of questions to generate
        
    Returns:
        List of generated questions
    """
    return ai_interview_service.generate_questions(job_post, resume, interview_type, num_questions)


def analyze_interview_response(question_id, response, session):
    """
    Analyze an interview response using AI service
    
    Args:
        question_id: ID of the question being answered
        response: Candidate's response text
        session: InterviewSession instance
        
    Returns:
        Analysis results
    """
    from .models import AIInterviewQuestion
    
    try:
        # Get the question
        question_obj = AIInterviewQuestion.objects.get(id=question_id, interview_session=session)
        
        # Update the question with the response
        question_obj.candidate_answer = response
        question_obj.save()
        
        # Analyze the response
        job_context = f"{session.application.job_post.title} at {session.application.job_post.recruiter.recruiter_profile.company_name}"
        analysis = ai_interview_service.analyze_response(question_obj.question_text, response, job_context)
        
        # Update the question with AI score
        question_obj.ai_score = analysis.get('score', 70)
        question_obj.save()
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing interview response: {str(e)}")
        return ai_interview_service._fallback_analysis(response)


def generate_interview_analysis(session):
    """
    Generate comprehensive interview session analysis
    
    Args:
        session: InterviewSession instance
        
    Returns:
        Comprehensive analysis results
    """
    # Get AI-based analysis
    ai_analysis = ai_interview_service.generate_session_analysis(session)
    
    # Get comprehensive scoring analysis
    scoring_analysis = interview_scoring_service.calculate_comprehensive_score(session)
    
    # Combine both analyses
    combined_analysis = {
        **ai_analysis,
        'detailed_scoring': scoring_analysis,
        'combined_score': scoring_analysis.get('overall_score', ai_analysis.get('overall_score', 70)),
        'analysis_timestamp': timezone.now().isoformat()
    }
    
    return combined_analysis


def get_interview_feedback(session):
    """
    Get detailed feedback for completed interview session
    
    Args:
        session: InterviewSession instance
        
    Returns:
        Detailed feedback and recommendations
    """
    return ai_interview_service.generate_session_analysis(session)
    
# =============================================================================
# INTERVIEW SCORING AND ANALYTICS
# =============================================================================

class InterviewScoringService:
    """
    Service for calculating comprehensive interview scores and analytics
    """
    
    def __init__(self):
        self.scoring_weights = {
            'technical_accuracy': 0.3,
            'communication_clarity': 0.25,
            'problem_solving': 0.2,
            'depth_of_knowledge': 0.15,
            'response_completeness': 0.1
        }
        
        self.difficulty_multipliers = {
            'easy': 0.8,
            'medium': 1.0,
            'hard': 1.2
        }
    
    def calculate_comprehensive_score(self, session):
        """
        Calculate comprehensive interview score with multiple criteria
        
        Args:
            session: InterviewSession instance
            
        Returns:
            Dictionary with detailed scoring breakdown
        """
        try:
            from .models import AIInterviewQuestion
            
            questions = AIInterviewQuestion.objects.filter(
                interview_session=session,
                candidate_answer__isnull=False
            ).exclude(candidate_answer='')
            
            if not questions.exists():
                return self._empty_score_result()
            
            # Calculate individual question scores
            question_scores = []
            total_weighted_score = 0
            total_weight = 0
            
            for question in questions:
                question_score = self._calculate_question_score(question)
                question_scores.append(question_score)
                
                # Apply difficulty multiplier
                difficulty_multiplier = self.difficulty_multipliers.get(
                    question.difficulty_level, 1.0
                )
                weighted_score = question_score['overall_score'] * difficulty_multiplier
                
                total_weighted_score += weighted_score
                total_weight += difficulty_multiplier
            
            # Calculate overall scores
            overall_score = total_weighted_score / total_weight if total_weight > 0 else 0
            
            # Calculate category averages
            category_scores = self._calculate_category_scores(question_scores)
            
            # Calculate performance metrics
            performance_metrics = self._calculate_performance_metrics(questions, question_scores)
            
            # Generate recommendations
            recommendations = self._generate_score_based_recommendations(
                overall_score, category_scores, performance_metrics
            )
            
            return {
                'overall_score': round(overall_score, 2),
                'category_scores': category_scores,
                'performance_metrics': performance_metrics,
                'question_scores': question_scores,
                'recommendations': recommendations,
                'scoring_methodology': {
                    'weights': self.scoring_weights,
                    'difficulty_multipliers': self.difficulty_multipliers
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating comprehensive score: {str(e)}")
            return self._empty_score_result()
    
    def _calculate_question_score(self, question):
        """Calculate detailed score for individual question"""
        response = question.candidate_answer
        response_length = len(response.split()) if response else 0
        
        # Base scoring criteria
        scores = {
            'technical_accuracy': self._assess_technical_accuracy(question, response),
            'communication_clarity': self._assess_communication_clarity(response),
            'problem_solving': self._assess_problem_solving(question, response),
            'depth_of_knowledge': self._assess_depth_of_knowledge(response),
            'response_completeness': self._assess_response_completeness(question, response)
        }
        
        # Calculate weighted overall score
        overall_score = sum(
            scores[criterion] * self.scoring_weights[criterion]
            for criterion in scores
        )
        
        return {
            'question_id': question.id,
            'question_type': question.question_type,
            'difficulty_level': question.difficulty_level,
            'overall_score': overall_score,
            'criterion_scores': scores,
            'response_length': response_length,
            'time_taken': question.time_taken_seconds,
            'ai_score': question.ai_score
        }
    
    def _assess_technical_accuracy(self, question, response):
        """Assess technical accuracy of response"""
        if question.question_type != 'technical':
            return 80  # Default for non-technical questions
        
        # Simple heuristics for technical accuracy
        technical_keywords = [
            'algorithm', 'data structure', 'complexity', 'optimization',
            'database', 'api', 'framework', 'architecture', 'design pattern'
        ]
        
        response_lower = response.lower()
        keyword_count = sum(1 for keyword in technical_keywords if keyword in response_lower)
        
        # Base score on keyword presence and response length
        base_score = min(90, 50 + (keyword_count * 8) + (len(response.split()) * 0.5))
        
        return max(30, min(100, base_score))
    
    def _assess_communication_clarity(self, response):
        """Assess clarity and structure of communication"""
        if not response:
            return 0
        
        words = response.split()
        sentences = response.split('.')
        
        # Factors for clarity assessment
        word_count = len(words)
        sentence_count = len([s for s in sentences if s.strip()])
        avg_sentence_length = word_count / max(1, sentence_count)
        
        # Scoring based on structure and length
        if word_count < 10:
            return 30  # Too brief
        elif word_count > 300:
            return 70  # Potentially too verbose
        elif 20 <= word_count <= 150:
            return 85  # Good length
        else:
            return 65  # Acceptable
    
    def _assess_problem_solving(self, question, response):
        """Assess problem-solving approach in response"""
        if not response:
            return 0
        
        problem_solving_indicators = [
            'approach', 'solution', 'step', 'process', 'method',
            'analyze', 'consider', 'evaluate', 'implement', 'strategy'
        ]
        
        response_lower = response.lower()
        indicator_count = sum(1 for indicator in problem_solving_indicators if indicator in response_lower)
        
        # Score based on problem-solving language and structure
        base_score = 40 + (indicator_count * 10)
        
        # Bonus for structured thinking (numbered points, etc.)
        if any(marker in response for marker in ['1.', '2.', 'first', 'second', 'then', 'next']):
            base_score += 15
        
        return max(20, min(100, base_score))
    
    def _assess_depth_of_knowledge(self, response):
        """Assess depth and detail of knowledge demonstrated"""
        if not response:
            return 0
        
        words = response.split()
        word_count = len(words)
        
        # Look for detailed explanations
        detail_indicators = [
            'because', 'since', 'due to', 'reason', 'example',
            'specifically', 'particularly', 'detail', 'explain'
        ]
        
        response_lower = response.lower()
        detail_count = sum(1 for indicator in detail_indicators if indicator in response_lower)
        
        # Score based on length and detail indicators
        length_score = min(40, word_count * 0.4)
        detail_score = detail_count * 8
        
        total_score = length_score + detail_score + 20  # Base score
        
        return max(10, min(100, total_score))
    
    def _assess_response_completeness(self, question, response):
        """Assess how completely the response addresses the question"""
        if not response:
            return 0
        
        # Simple heuristic based on response length relative to question complexity
        question_words = len(question.question_text.split())
        response_words = len(response.split())
        
        # Expected response length based on question length
        expected_length = max(20, question_words * 2)
        
        if response_words >= expected_length:
            return 90
        elif response_words >= expected_length * 0.7:
            return 75
        elif response_words >= expected_length * 0.5:
            return 60
        else:
            return 40
    
    def _calculate_category_scores(self, question_scores):
        """Calculate average scores by category"""
        if not question_scores:
            return {}
        
        categories = {}
        for score in question_scores:
            for criterion, value in score['criterion_scores'].items():
                if criterion not in categories:
                    categories[criterion] = []
                categories[criterion].append(value)
        
        return {
            criterion: round(sum(values) / len(values), 2)
            for criterion, values in categories.items()
        }
    
    def _calculate_performance_metrics(self, questions, question_scores):
        """Calculate additional performance metrics"""
        if not question_scores:
            return {}
        
        total_questions = questions.count()
        answered_questions = len(question_scores)
        
        # Time analysis
        total_time = sum(q.time_taken_seconds for q in questions if q.time_taken_seconds)
        avg_time_per_question = total_time / max(1, answered_questions)
        
        # Score distribution
        scores = [qs['overall_score'] for qs in question_scores]
        
        # Difficulty analysis
        difficulty_performance = {}
        for score in question_scores:
            difficulty = score['difficulty_level']
            if difficulty not in difficulty_performance:
                difficulty_performance[difficulty] = []
            difficulty_performance[difficulty].append(score['overall_score'])
        
        difficulty_averages = {
            difficulty: round(sum(scores) / len(scores), 2)
            for difficulty, scores in difficulty_performance.items()
        }
        
        return {
            'completion_rate': round((answered_questions / total_questions) * 100, 1),
            'score_range': {
                'min': min(scores) if scores else 0,
                'max': max(scores) if scores else 0
            },
            'total_time_minutes': round(total_time / 60, 1),
            'average_time_per_question': round(avg_time_per_question / 60, 1),
            'difficulty_performance': difficulty_averages,
            'consistency_score': self._calculate_consistency_score(scores)
        }
    
    def _calculate_consistency_score(self, scores):
        """Calculate how consistent the performance was across questions"""
        if len(scores) < 2:
            return 100
        
        # Calculate standard deviation
        mean_score = sum(scores) / len(scores)
        variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)
        std_dev = variance ** 0.5
        
        # Convert to consistency score (lower std_dev = higher consistency)
        consistency = max(0, 100 - (std_dev * 2))
        return round(consistency, 2)
    
    def _generate_score_based_recommendations(self, overall_score, category_scores, performance_metrics):
        """Generate recommendations based on scoring analysis"""
        recommendations = []
        
        # Overall performance recommendations
        if overall_score >= 85:
            recommendations.append("Excellent performance! You demonstrate strong competency across all areas.")
        elif overall_score >= 70:
            recommendations.append("Good performance with room for improvement in specific areas.")
        elif overall_score >= 55:
            recommendations.append("Average performance. Focus on strengthening key competencies.")
        else:
            recommendations.append("Performance needs improvement. Consider additional preparation and practice.")
        
        # Category-specific recommendations
        for category, score in category_scores.items():
            if score < 60:
                category_name = category.replace('_', ' ').title()
                recommendations.append(f"Focus on improving {category_name} - current score: {score}")
        
        # Time management recommendations
        avg_time = performance_metrics.get('average_time_per_question', 0)
        if avg_time > 10:
            recommendations.append("Consider working on time management - responses took longer than optimal.")
        elif avg_time < 2:
            recommendations.append("Consider providing more detailed responses - quick answers may lack depth.")
        
        # Consistency recommendations
        consistency = performance_metrics.get('consistency_score', 100)
        if consistency < 70:
            recommendations.append("Work on maintaining consistent performance across different question types.")
        
        return recommendations
    
    def _empty_score_result(self):
        """Return empty score result for error cases"""
        return {
            'overall_score': 0,
            'category_scores': {},
            'performance_metrics': {},
            'question_scores': [],
            'recommendations': ['Unable to calculate score - no valid responses found.'],
            'scoring_methodology': {
                'weights': self.scoring_weights,
                'difficulty_multipliers': self.difficulty_multipliers
            }
        }


# Initialize scoring service
interview_scoring_service = InterviewScoringService()


def calculate_interview_score(session):
    """
    Calculate comprehensive interview score
    
    Args:
        session: InterviewSession instance
        
    Returns:
        Detailed scoring analysis
    """
    return interview_scoring_service.calculate_comprehensive_score(session)


# =============================================================================
# INTERVIEW SESSION CLEANUP AND ARCHIVAL
# =============================================================================

def cleanup_interview_sessions():
    """
    Cleanup and archive old interview sessions
    
    Returns:
        Dictionary with cleanup statistics
    """
    try:
        from .models import InterviewSession, AIInterviewQuestion
        from django.utils import timezone
        from datetime import timedelta
        
        # Define cleanup criteria
        cutoff_date = timezone.now() - timedelta(days=90)  # Archive sessions older than 90 days
        expired_cutoff = timezone.now() - timedelta(hours=2)  # Cancel sessions inactive for 2+ hours
        
        # Find sessions to cleanup
        old_completed_sessions = InterviewSession.objects.filter(
            status='completed',
            updated_at__lt=cutoff_date
        )
        
        expired_in_progress_sessions = InterviewSession.objects.filter(
            status='in_progress',
            created_at__lt=expired_cutoff
        )
        
        # Archive old completed sessions
        archived_count = 0
        for session in old_completed_sessions:
            # Create archive record (you might want to move to separate archive table)
            session.notes = session.notes or ''
            session.notes += f'\nARCHIVED at {timezone.now().isoformat()}'
            session.save()
            archived_count += 1
        
        # Cancel expired in-progress sessions
        cancelled_count = expired_in_progress_sessions.update(
            status='cancelled',
            notes=models.F('notes') + f'\nAUTO-CANCELLED due to inact at {timezone.now().isoformat()}'
        )
        
        # Cleanup orphaned questions (questions without sessions)
        orphaned_questions = AIInterviewQuestion.objects.filter(
            interview_session__isnull=True
        )
        orphaned_count = orphaned_questions.count()
        orphaned_questions.delete()
        
        logger.info(f"Interview cleanup completed: {archived_count} archived, {cancelled_count} cancelled, {orphaned_count} orphaned questions removed")
        
        return {
            'success': True,
            'archived_sessions': archived_count,
            'cancelled_sessions': cancelled_count,
            'orphaned_questions_removed': orphaned_count,
            'cleanup_timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error during interview session cleanup: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'cleanup_timestamp': timezone.now().isoformat()
        }