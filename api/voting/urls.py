from django.urls import path

from voting.views import (
    BallotDetailView,
    BallotDirectoryView,
    BallotVotesView,
    YearResultsAuditView,
    YearResultsView,
)

urlpatterns = [
    path(
        'years/<int:year>/ballot/',
        BallotDetailView.as_view(),
        name='ballot-detail',
    ),
    path(
        'years/<int:year>/ballot/votes/',
        BallotVotesView.as_view(),
        name='ballot-votes',
    ),
    path(
        'years/<int:year>/ballot/directory/',
        BallotDirectoryView.as_view(),
        name='ballot-directory',
    ),
    path(
        'years/<int:year>/results/audit/',
        YearResultsAuditView.as_view(),
        name='year-results-audit',
    ),
    path(
        'years/<int:year>/results/',
        YearResultsView.as_view(),
        name='year-results',
    ),
]
