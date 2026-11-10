from rest_framework import serializers

from awards.models import Award
from awards.serializers import AwardCriterionSerializer, NomineePublicSerializer
from people.models import OrgPerson
from voting.models import Vote


class VoterProfileSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(read_only=True)

    class Meta:
        model = OrgPerson
        fields = (
            'id',
            'email',
            'first_name',
            'last_name',
            'display_name',
            'company',
            'electorate',
            'department_name',
        )


class BallotAwardSerializer(serializers.ModelSerializer):
    criteria = AwardCriterionSerializer(many=True, read_only=True)
    nominees = serializers.SerializerMethodField()
    current_vote = serializers.SerializerMethodField()

    class Meta:
        model = Award
        fields = (
            'slug',
            'name',
            'description',
            'ideal_winner',
            'division',
            'voting_mode',
            'executive_weight',
            'staff_weight',
            'sort_order',
            'criteria',
            'nominees',
            'current_vote',
        )

    def get_nominees(self, obj):
        if obj.voting_mode == Award.VotingMode.STAFF_OPEN:
            return []
        confirmed = [n for n in obj.nominees.all() if n.is_confirmed]
        return NomineePublicSerializer(confirmed, many=True).data

    def get_current_vote(self, obj):
        votes_by_award = self.context.get('votes_by_award') or {}
        vote = votes_by_award.get(obj.id)
        if vote is None:
            return None
        return VoteChoiceSerializer(vote).data


class VoteChoiceSerializer(serializers.ModelSerializer):
    award_slug = serializers.CharField(source='award.slug', read_only=True)
    nominee_id = serializers.IntegerField(read_only=True, allow_null=True)
    selected_person_id = serializers.IntegerField(read_only=True, allow_null=True)
    selected_person_name = serializers.SerializerMethodField()

    class Meta:
        model = Vote
        fields = (
            'award_slug',
            'nominee_id',
            'selected_person_id',
            'selected_person_name',
            'electorate_at_vote',
            'updated_at',
        )

    def get_selected_person_name(self, obj):
        if obj.selected_person_id is None:
            return None
        return obj.selected_person.display_name


class VoteSubmitItemSerializer(serializers.Serializer):
    award_slug = serializers.SlugField()
    nominee_id = serializers.IntegerField(required=False, allow_null=True)
    selected_person_id = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, attrs):
        has_nominee = attrs.get('nominee_id') is not None
        has_selected = attrs.get('selected_person_id') is not None
        if has_nominee == has_selected:
            raise serializers.ValidationError(
                'Provide exactly one of nominee_id or selected_person_id.'
            )
        return attrs


class VoteSubmitSerializer(serializers.Serializer):
    votes = VoteSubmitItemSerializer(many=True)

    def validate_votes(self, value):
        if not value:
            raise serializers.ValidationError('votes must be a non-empty list.')
        slugs = [item['award_slug'] for item in value]
        if len(slugs) != len(set(slugs)):
            raise serializers.ValidationError('Duplicate award_slug in payload.')
        return value


class DirectoryPersonSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(read_only=True)

    class Meta:
        model = OrgPerson
        fields = (
            'id',
            'first_name',
            'last_name',
            'display_name',
            'department_name',
            'company',
        )
