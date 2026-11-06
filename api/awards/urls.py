from django.urls import path

from awards.views import (
    YearAwardDetailView,
    YearAwardListView,
    YearDetailView,
    YearListView,
)

urlpatterns = [
    path('years/', YearListView.as_view(), name='year-list'),
    path('years/<int:year>/', YearDetailView.as_view(), name='year-detail'),
    path(
        'years/<int:year>/awards/',
        YearAwardListView.as_view(),
        name='year-award-list',
    ),
    path(
        'years/<int:year>/awards/<slug:slug>/',
        YearAwardDetailView.as_view(),
        name='year-award-detail',
    ),
]
