from django.db.models import Count, Q
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from awards.models import Award, AwardYear
from awards.serializers import (
    AwardDetailSerializer,
    AwardListSerializer,
    AwardYearDetailSerializer,
    AwardYearListSerializer,
)


class YearListView(ListAPIView):
    """GET /api/v1/years/ — public year catalogue."""

    permission_classes = [AllowAny]
    serializer_class = AwardYearListSerializer
    queryset = AwardYear.objects.all()


class YearDetailView(RetrieveAPIView):
    """GET /api/v1/years/{year}/ — year detail with counts."""

    permission_classes = [AllowAny]
    serializer_class = AwardYearDetailSerializer
    lookup_field = 'year'
    lookup_url_kwarg = 'year'

    def get_queryset(self):
        return AwardYear.objects.annotate(
            awards_count=Count(
                'awards',
                filter=Q(awards__is_active=True),
                distinct=True,
            ),
        )


class YearAwardListView(ListAPIView):
    """GET /api/v1/years/{year}/awards/ — active awards for a year."""

    permission_classes = [AllowAny]
    serializer_class = AwardListSerializer

    def get_year(self):
        return AwardYear.objects.filter(year=self.kwargs['year']).first()

    def list(self, request, *args, **kwargs):
        if self.get_year() is None:
            return Response(
                {'detail': 'Not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        qs = Award.objects.filter(
            year__year=self.kwargs['year'],
            is_active=True,
        ).order_by('sort_order', 'name')

        division = self.request.query_params.get('division')
        if division:
            qs = qs.filter(division=division)
        return qs


class YearAwardDetailView(APIView):
    """GET /api/v1/years/{year}/awards/{slug}/ — award detail (public)."""

    permission_classes = [AllowAny]

    def get(self, request, year, slug):
        award = (
            Award.objects.filter(
                year__year=year,
                slug=slug,
                is_active=True,
            )
            .select_related('year')
            .prefetch_related('criteria')
            .first()
        )
        if award is None:
            return Response(
                {'detail': 'Not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(AwardDetailSerializer(award).data)
