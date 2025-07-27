"""
Search analytics and tracking models for advanced search optimization
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()


class SearchAnalytics(models.Model):
    """
    Model for tracking search queries and analytics
    """
    SEARCH_TYPES = (
        ('jobs', 'Job Search'),
        ('candidates', 'Candidate Search'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='search_analytics')
    search_type = models.CharField(max_length=20, choices=SEARCH_TYPES)
    query = models.TextField(blank=True)
    filters_applied = models.JSONField(default=dict)
    
    # Results and interaction data
    results_count = models.IntegerField(default=0)
    clicked_results = models.JSONField(default=list)  # List of clicked result IDs
    search_duration = models.FloatField(default=0.0)  # Time spent on search results page
    
    # Technical data
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    session_id = models.CharField(max_length=40, blank=True)
    
    # Timestamps
    searched_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-searched_at']
        indexes = [
            models.Index(fields=['search_type', 'searched_at']),
            models.Index(fields=['user', 'searched_at']),
            models.Index(fields=['query', 'search_type']),
        ]
    
    def __str__(self):
        return f"{self.get_search_type_display()} - '{self.query}' by {self.user.username if self.user else 'Anonymous'}"


class PopularSearchTerms(models.Model):
    """
    Model for tracking popular search terms and suggestions
    """
    SEARCH_TYPES = (
        ('jobs', 'Job Search'),
        ('candidates', 'Candidate Search'),
    )
    
    search_type = models.CharField(max_length=20, choices=SEARCH_TYPES)
    term = models.CharField(max_length=255, db_index=True)
    search_count = models.IntegerField(default=1)
    click_through_rate = models.FloatField(default=0.0)  # Percentage of searches that resulted in clicks
    last_searched = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('search_type', 'term')
        ordering = ['-search_count', '-last_searched']
        indexes = [
            models.Index(fields=['search_type', 'search_count']),
            models.Index(fields=['term', 'search_type']),
        ]
    
    def __str__(self):
        return f"{self.term} ({self.search_count} searches)"


class SearchSuggestions(models.Model):
    """
    Model for storing search suggestions and autocomplete data
    """
    SEARCH_TYPES = (
        ('jobs', 'Job Search'),
        ('candidates', 'Candidate Search'),
    )
    
    SUGGESTION_TYPES = (
        ('query', 'Query Suggestion'),
        ('skill', 'Skill Suggestion'),
        ('location', 'Location Suggestion'),
        ('company', 'Company Suggestion'),
        ('title', 'Job Title Suggestion'),
    )
    
    search_type = models.CharField(max_length=20, choices=SEARCH_TYPES)
    suggestion_type = models.CharField(max_length=20, choices=SUGGESTION_TYPES)
    text = models.CharField(max_length=255, db_index=True)
    popularity_score = models.FloatField(default=0.0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('search_type', 'suggestion_type', 'text')
        ordering = ['-popularity_score', 'text']
        indexes = [
            models.Index(fields=['search_type', 'suggestion_type', 'is_active']),
            models.Index(fields=['text', 'search_type']),
            models.Index(fields=['popularity_score', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.text} ({self.get_suggestion_type_display()})"


class UserSearchPreferences(models.Model):
    """
    Model for storing user search preferences and history
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='search_preferences')
    
    # Saved search filters
    default_job_filters = models.JSONField(default=dict)
    default_candidate_filters = models.JSONField(default=dict)
    
    # Search behavior preferences
    results_per_page = models.IntegerField(default=20)
    sort_preference = models.CharField(
        max_length=20,
        choices=[
            ('relevance', 'Relevance'),
            ('date', 'Date Posted'),
            ('salary', 'Salary'),
            ('popularity', 'Popularity'),
        ],
        default='relevance'
    )
    
    # Notification preferences for saved searches
    email_alerts_enabled = models.BooleanField(default=False)
    alert_frequency = models.CharField(
        max_length=20,
        choices=[
            ('immediate', 'Immediate'),
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
        ],
        default='daily'
    )
    
    # Recent searches (stored as JSON for quick access)
    recent_job_searches = models.JSONField(default=list)
    recent_candidate_searches = models.JSONField(default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Search preferences for {self.user.username}"
    
    def add_recent_search(self, search_type: str, query: str, filters: dict):
        """
        Add a search to recent searches history
        """
        search_data = {
            'query': query,
            'filters': filters,
            'timestamp': timezone.now().isoformat()
        }
        
        if search_type == 'jobs':
            self.recent_job_searches.insert(0, search_data)
            self.recent_job_searches = self.recent_job_searches[:10]  # Keep only last 10
        elif search_type == 'candidates':
            self.recent_candidate_searches.insert(0, search_data)
            self.recent_candidate_searches = self.recent_candidate_searches[:10]  # Keep only last 10
        
        self.save(update_fields=['recent_job_searches', 'recent_candidate_searches'])


class SavedSearch(models.Model):
    """
    Model for user saved searches with alerts
    """
    SEARCH_TYPES = (
        ('jobs', 'Job Search'),
        ('candidates', 'Candidate Search'),
    )
    
    ALERT_FREQUENCIES = (
        ('immediate', 'Immediate'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_searches')
    name = models.CharField(max_length=255)
    search_type = models.CharField(max_length=20, choices=SEARCH_TYPES)
    query = models.TextField(blank=True)
    filters = models.JSONField(default=dict)
    
    # Alert settings
    alerts_enabled = models.BooleanField(default=True)
    alert_frequency = models.CharField(max_length=20, choices=ALERT_FREQUENCIES, default='daily')
    last_alert_sent = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['search_type', 'alerts_enabled']),
            models.Index(fields=['alert_frequency', 'last_alert_sent']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.user.username}"
    
    def should_send_alert(self) -> bool:
        """
        Check if an alert should be sent based on frequency settings
        """
        if not self.alerts_enabled or not self.is_active:
            return False
        
        if not self.last_alert_sent:
            return True
        
        now = timezone.now()
        time_diff = now - self.last_alert_sent
        
        if self.alert_frequency == 'immediate':
            return True
        elif self.alert_frequency == 'daily':
            return time_diff.days >= 1
        elif self.alert_frequency == 'weekly':
            return time_diff.days >= 7
        elif self.alert_frequency == 'monthly':
            return time_diff.days >= 30
        
        return False