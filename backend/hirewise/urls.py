"""
URL configuration for hirewise project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
    TokenBlacklistView,
)
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from matcher.health_views import (
    HealthCheckView,
    DetailedHealthCheckView,
    ReadinessCheckView,
    LivenessCheckView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    
    # Health Check endpoints (for monitoring and load balancers)
    path("health/", HealthCheckView.as_view(), name="health-check"),
    path("api/health/", DetailedHealthCheckView.as_view(), name="detailed-health-check"),
    path("ready/", ReadinessCheckView.as_view(), name="readiness-check"),
    path("live/", LivenessCheckView.as_view(), name="liveness-check"),
    
    # API Documentation (version-specific)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema-v1"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/v1/docs/", SpectacularSwaggerView.as_view(url_name="schema-v1"), name="swagger-ui-v1"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("api/v1/redoc/", SpectacularRedocView.as_view(url_name="schema-v1"), name="redoc-v1"),
    
    # Versioned API endpoints
    path("api/v1/", include(("matcher.urls", "matcher"), namespace="v1")),
    path("api/", include(("matcher.urls", "matcher"), namespace="default")),  # Default to v1 for backward compatibility
    
    # DRF browsable API
    path("api-auth/", include("rest_framework.urls")),
    
    # JWT Authentication endpoints (versioned)
    path("api/v1/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair_v1"),
    path("api/v1/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh_v1"),
    path("api/v1/auth/token/verify/", TokenVerifyView.as_view(), name="token_verify_v1"),
    path("api/v1/auth/token/blacklist/", TokenBlacklistView.as_view(), name="token_blacklist_v1"),
    
    # Legacy endpoints (for backward compatibility)
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/auth/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("api/auth/token/blacklist/", TokenBlacklistView.as_view(), name="token_blacklist"),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
