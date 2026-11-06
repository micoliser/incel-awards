from django.urls import path

from people.views import DevOrgUsersView

urlpatterns = [
    # Match production: GET /api/v1/external/users (+ optional trailing slash)
    path('external/users', DevOrgUsersView.as_view(), name='external-org-users'),
    path('external/users/', DevOrgUsersView.as_view(), name='external-org-users-slash'),
]
