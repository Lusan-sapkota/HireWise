from django.apps import AppConfig


class MatcherConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "matcher"
    
    def ready(self):
        """Import signals when the app is ready."""
        import matcher.signals
