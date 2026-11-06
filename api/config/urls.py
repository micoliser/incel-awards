from django.contrib import admin
from django.urls import include, path
from django.conf import settings

from config.views import health

admin_path = getattr(settings, 'DJANGO_ADMIN_URL', 'admin/').strip('/') + '/'

urlpatterns = [
    path(admin_path, admin.site.urls),
    path('api/v1/health/', health, name='health'),
    path('api/v1/', include('awards.urls')),
    path('api/v1/', include('voting.urls')),
    path('api/v1/', include('people.urls')),
]
