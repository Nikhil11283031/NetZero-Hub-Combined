"""Counts for the "My Services Dashboard" page: one number per NetZero Hub service."""
from django.apps import apps
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView


class DashboardView(APIView):
    """Active requests the signed-in user has in each service."""

    @extend_schema(responses=inline_serializer("DashboardCounts", {
        "recycling_count": serializers.IntegerField(),
        "environment_count": serializers.IntegerField(),
        "solar_count": serializers.IntegerField(),
    }))
    def get(self, request):
        user = request.user
        counts = {"recycling_count": 0, "environment_count": 0, "solar_count": 0}

        if apps.is_installed("recycling"):
            from recycling.models import Booking
            counts["recycling_count"] = Booking.objects.filter(user=user, status__in=Booking.ACTIVE_STATUSES).count()

        # The React dashboard reads solar and EPA counts from their own services (solar-service and the two
        # EPA APIs), each with its own database. solar_count stays here only for compatibility.
        # This legacy placeholder is retained for compatibility, not used by that card.
        return Response(counts)
