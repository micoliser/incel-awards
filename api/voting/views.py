import secrets

from django.db import transaction
from django.db.models import Prefetch, Q
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed, NotFound, PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from awards.models import Award, AwardYear, Nominee
from awards.serializers import voting_window_status
from emails.services.vote_confirmation_emails import queue_vote_confirmation_email
from people.models import OrgPerson
from voting.authentication import authenticate_ballot, get_year_or_404
from voting.serializers import (
    BallotAwardSerializer,
    DirectoryPersonSerializer,
    VoteChoiceSerializer,
    VoteSubmitSerializer,
    VoterProfileSerializer,
)
from voting.services.audit import build_year_audit
from voting.services.eligibility import awards_for_voter
from voting.services.tally import tally_year
from voting.models import BallotToken, Vote
from voting.services.votes import (
    VoteValidationError,
    ballot_is_submitted,
    ballot_writes_allowed,
    upsert_votes,
)
from voting.throttling import (
    BallotDirectoryRateThrottle,
    BallotResolveRateThrottle,
    BallotVoteRateThrottle,
)


def _ballot_payload(
    year: AwardYear,
    person: OrgPerson,
    ballot_token: BallotToken | None = None,
) -> dict:
    allowed = awards_for_voter(person, year)
    award_ids = [a.id for a in allowed]
    # Prefetch nominees for serializer
    awards = (
        Award.objects.filter(id__in=award_ids)
        .prefetch_related(
            'criteria',
            Prefetch(
                'nominees',
                queryset=Nominee.objects.order_by('sort_order', 'id'),
            ),
        )
        .order_by('sort_order', 'name')
    )
    votes = Vote.objects.filter(voter=person, award_id__in=award_ids).select_related(
        'award',
        'selected_person',
        'nominee',
    )
    votes_by_award = {v.award_id: v for v in votes}
    is_submitted = ballot_is_submitted(ballot_token)

    return {
        'year': year.year,
        'title': year.title,
        'status': year.status,
        'voting_opens_at': year.voting_opens_at,
        'voting_closes_at': year.voting_closes_at,
        'voting_window_status': voting_window_status(year),
        'writes_allowed': ballot_writes_allowed(year, ballot_token),
        'is_submitted': is_submitted,
        'submitted_at': ballot_token.submitted_at if ballot_token else None,
        'voter': VoterProfileSerializer(person).data,
        'awards': BallotAwardSerializer(
            awards,
            many=True,
            context={'votes_by_award': votes_by_award},
        ).data,
        'votes': VoteChoiceSerializer(list(votes_by_award.values()), many=True).data,
    }


class BallotDetailView(APIView):
    """GET /api/v1/years/{year}/ballot/ — voter profile + allowed awards + votes."""

    permission_classes = [AllowAny]
    throttle_classes = [BallotResolveRateThrottle]

    def get(self, request, year):
        try:
            award_year, ballot_token, person = authenticate_ballot(request, year)
        except AuthenticationFailed as exc:
            return Response({'detail': str(exc.detail)}, status=status.HTTP_401_UNAUTHORIZED)
        except PermissionDenied as exc:
            return Response({'detail': str(exc.detail)}, status=status.HTTP_403_FORBIDDEN)
        except NotFound as exc:
            return Response({'detail': str(exc.detail)}, status=status.HTTP_404_NOT_FOUND)

        return Response(_ballot_payload(award_year, person, ballot_token))


class BallotVotesView(APIView):
    """PUT /api/v1/years/{year}/ballot/votes/ — final ballot submit (no edits after)."""

    permission_classes = [AllowAny]
    throttle_classes = [BallotVoteRateThrottle]

    def put(self, request, year):
        try:
            award_year, ballot_token, person = authenticate_ballot(request, year)
        except AuthenticationFailed as exc:
            return Response({'detail': str(exc.detail)}, status=status.HTTP_401_UNAUTHORIZED)
        except PermissionDenied as exc:
            return Response({'detail': str(exc.detail)}, status=status.HTTP_403_FORBIDDEN)
        except NotFound as exc:
            return Response({'detail': str(exc.detail)}, status=status.HTTP_404_NOT_FOUND)

        serializer = VoteSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = upsert_votes(
                year=award_year,
                voter=person,
                items=serializer.validated_data['votes'],
                ballot_token=ballot_token,
            )
        except VoteValidationError as exc:
            http_status = status.HTTP_403_FORBIDDEN if exc.code in (
                'window_closed',
                'division_forbidden',
                'ineligible_voter',
                'already_submitted',
            ) else status.HTTP_400_BAD_REQUEST
            return Response(
                {'detail': exc.message, 'code': exc.code},
                status=http_status,
            )

        award_count = len(result.votes)
        token_id = ballot_token.pk
        transaction.on_commit(
            lambda: queue_vote_confirmation_email(token_id, award_count)
        )

        ballot_token.refresh_from_db()
        return Response(_ballot_payload(award_year, person, ballot_token))


class BallotDirectoryView(APIView):
    """GET /api/v1/years/{year}/ballot/directory/ — search Nigeria-eligible people."""

    permission_classes = [AllowAny]
    throttle_classes = [BallotDirectoryRateThrottle]

    def get(self, request, year):
        try:
            _award_year, _token, _person = authenticate_ballot(request, year)
        except AuthenticationFailed as exc:
            return Response({'detail': str(exc.detail)}, status=status.HTTP_401_UNAUTHORIZED)
        except PermissionDenied as exc:
            return Response({'detail': str(exc.detail)}, status=status.HTTP_403_FORBIDDEN)
        except NotFound as exc:
            return Response({'detail': str(exc.detail)}, status=status.HTTP_404_NOT_FOUND)

        qs = OrgPerson.objects.filter(
            is_active=True,
            is_nigeria_eligible=True,
        ).order_by('last_name', 'first_name')

        q = (request.query_params.get('q') or '').strip()
        if q:
            qs = qs.filter(
                Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
                | Q(email__icontains=q)
                | Q(department_name__icontains=q)
            )

        try:
            limit = min(int(request.query_params.get('limit', 50)), 100)
        except (TypeError, ValueError):
            limit = 50

        people = qs[:limit]
        return Response({
            'count': len(people),
            'results': DirectoryPersonSerializer(people, many=True).data,
        })


def _extract_results_preview_token(request) -> str:
    raw = (request.query_params.get('preview') or '').strip()
    if raw:
        return raw
    header = (request.headers.get('X-Results-Preview-Token') or '').strip()
    return header


def _preview_token_ok(award_year: AwardYear, request) -> bool:
    preview_token = _extract_results_preview_token(request)
    stored = (award_year.results_preview_token or '').strip()
    return bool(
        preview_token
        and stored
        and secrets.compare_digest(preview_token, stored)
    )


class YearResultsView(APIView):
    """
    GET /api/v1/years/{year}/results/

    Public when results_published_at is set.
    Committee preview when ?preview=<results_preview_token> (or header) matches.
    Otherwise 403. Missing year → 404.
    """

    permission_classes = [AllowAny]

    def get(self, request, year):
        try:
            award_year = get_year_or_404(year)
        except NotFound as exc:
            return Response({'detail': str(exc.detail)}, status=status.HTTP_404_NOT_FOUND)

        published = award_year.results_published_at is not None
        preview_ok = _preview_token_ok(award_year, request)

        if not published and not preview_ok:
            return Response(
                {'detail': 'Results are not published yet.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        tallies = [t.to_dict() for t in tally_year(award_year)]
        return Response({
            'year': award_year.year,
            'title': award_year.title,
            'results_published_at': award_year.results_published_at,
            'preview': preview_ok and not published,
            'awards': tallies,
        })


class YearResultsAuditView(APIView):
    """
    GET /api/v1/years/{year}/results/audit/?preview=<token>

    Full committee audit (ballots, weighted maths, change log).
    Always requires the results preview token — never public, even after publish.
    """

    permission_classes = [AllowAny]

    def get(self, request, year):
        try:
            award_year = get_year_or_404(year)
        except NotFound as exc:
            return Response({'detail': str(exc.detail)}, status=status.HTTP_404_NOT_FOUND)

        if not _preview_token_ok(award_year, request):
            return Response(
                {'detail': 'Committee audit requires a valid preview token.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(build_year_audit(award_year))
