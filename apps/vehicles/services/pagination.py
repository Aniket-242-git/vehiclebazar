"""Configurable pagination for the vehicle API/list pages.

Page size defaults to settings.PAGINATION_DEFAULT_PAGE_SIZE (12) and is capped
at settings.PAGINATION_MAX_PAGE_SIZE so clients cannot request huge datasets.
Pagination happens at the queryset level via PageNumberPagination.
"""
from __future__ import annotations

from collections import OrderedDict

from django.conf import settings
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class VehiclePageNumberPagination(PageNumberPagination):
    page_size_query_param = "page_size"

    def get_page_size(self, request) -> int:
        default = getattr(settings, "PAGINATION_DEFAULT_PAGE_SIZE", 12)
        maximum = getattr(settings, "PAGINATION_MAX_PAGE_SIZE", 48)
        raw = request.query_params.get(self.page_size_query_param)
        if raw is None:
            return default
        try:
            size = int(raw)
        except (TypeError, ValueError):
            return default
        return max(1, min(size, maximum))

    def get_paginated_response(self, data):
        return Response(
            OrderedDict(
                [
                    ("count", self.page.paginator.count),
                    ("total_pages", self.page.paginator.num_pages),
                    ("current_page", self.page.number),
                    ("page_size", self.get_page_size(self.request)),
                    ("next", self.get_next_link()),
                    ("previous", self.get_previous_link()),
                    ("results", data),
                ]
            )
        )
