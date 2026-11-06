from django.utils import timezone
from rest_framework import serializers

from awards.models import Award, AwardCriterion, AwardYear, Nominee


def voting_window_status(year: AwardYear, now=None) -> str:
    """Relative status of the year voting window for public display."""
    now = now or timezone.now()
    opens = year.voting_opens_at
    closes = year.voting_closes_at
    if opens and now < opens:
        return 'upcoming'
    if closes and now >= closes:
        return 'closed'
    if opens and (closes is None or now < closes):
        return 'open'
    return year.status


class AwardYearListSerializer(serializers.ModelSerializer):
    class Meta:
        model = AwardYear
        fields = (
            'year',
            'title',
            'slug',
            'status',
            'voting_opens_at',
            'voting_closes_at',
        )


class AwardYearDetailSerializer(serializers.ModelSerializer):
    awards_count = serializers.IntegerField(read_only=True)
    confirmed_nominees_count = serializers.IntegerField(read_only=True)
    voting_window_status = serializers.SerializerMethodField()

    class Meta:
        model = AwardYear
        fields = (
            'year',
            'title',
            'slug',
            'status',
            'description',
            'voting_opens_at',
            'voting_closes_at',
            'results_published_at',
            'awards_count',
            'confirmed_nominees_count',
            'voting_window_status',
        )

    def get_voting_window_status(self, obj):
        return voting_window_status(obj)


class AwardListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Award
        fields = (
            'slug',
            'name',
            'description',
            'division',
            'voting_mode',
            'executive_weight',
            'staff_weight',
            'sort_order',
            'is_active',
        )


class AwardCriterionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AwardCriterion
        fields = ('id', 'label', 'weight_percent', 'sort_order')


class NomineePublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nominee
        fields = (
            'id',
            'nominee_type',
            'display_name',
            'justification',
            'basis_for_nomination',
            'sort_order',
        )


class AwardDetailSerializer(serializers.ModelSerializer):
    criteria = AwardCriterionSerializer(many=True, read_only=True)
    nominees = serializers.SerializerMethodField()
    voting_rules = serializers.SerializerMethodField()
    year = serializers.IntegerField(source='year.year', read_only=True)
    voting_window_status = serializers.SerializerMethodField()

    class Meta:
        model = Award
        fields = (
            'year',
            'slug',
            'name',
            'description',
            'division',
            'voting_mode',
            'executive_weight',
            'staff_weight',
            'sort_order',
            'is_active',
            'voting_rules',
            'voting_window_status',
            'criteria',
            'nominees',
        )

    def get_nominees(self, obj):
        confirmed = [
            n for n in obj.nominees.all() if n.is_confirmed
        ]
        return NomineePublicSerializer(confirmed, many=True).data

    def get_voting_rules(self, obj):
        return {
            'division': obj.division,
            'mode': obj.voting_mode,
            'executive_weight': obj.executive_weight,
            'staff_weight': obj.staff_weight,
        }

    def get_voting_window_status(self, obj):
        return voting_window_status(obj.year)
