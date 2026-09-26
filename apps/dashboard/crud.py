"""Generic CRUD helpers for the custom admin panel.

Keeps the per-entity views thin: each one only supplies a form class,
queryset, template names and (optionally) extra context.
"""
from __future__ import annotations

from typing import Any, Callable, Optional

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST


def crud_list(
    request,
    *,
    queryset: QuerySet,
    template_name: str,
    search_fields: list[str],
    q_param: str = "q",
    paginate_by: int = 20,
    order_param: str = "order",
    order_choices: Optional[dict[str, tuple[str, ...]]] = None,
    default_order: tuple[str, ...] = ("-created_at",),
    extra_context: Optional[Callable[[request], dict[str, Any]]] = None,
    page_meta: Optional[dict[str, Any]] = None,
):
    """List view with DB-level search, sorting and pagination."""
    qs = queryset
    q = request.GET.get(q_param, "").strip()
    if q and search_fields:
        from django.db.models import Q

        query = Q()
        for field in search_fields:
            query |= Q(**{f"{field}__icontains": q})
        qs = qs.filter(query)

    sort_key = ""
    current_order = default_order
    if order_choices:
        sort_key = request.GET.get(order_param, "").strip()
        if sort_key in order_choices:
            current_order = order_choices[sort_key]
    qs = qs.order_by(*current_order)

    paginator = Paginator(qs, paginate_by)
    page_obj = paginator.get_page(request.GET.get("page"))

    import urllib.parse as _up
    skip_keys = {q_param, "page"}
    if order_choices:
        skip_keys.add(order_param)
    qs_pairs = [(k, v) for k, v in request.GET.items() if k not in skip_keys]
    context: dict[str, Any] = {
        "querystring_no_page": "&".join(f"{_up.quote(k)}={_up.quote(str(v))}" for k, v in qs_pairs) + ("&" if qs_pairs else ""),
        "items": page_obj,
        "page_obj": page_obj,
        "q": q,
        "sort": sort_key,
    }
    if order_choices:
        context["order_choices"] = order_choices
    if page_meta:
        context.update(page_meta)
    if extra_context:
        context.update(extra_context(request))
    return render(request, template_name, context)


def crud_form(
    request,
    *,
    form_class,
    instance=None,
    template_name: str,
    success_url_name: str,
    success_message: str,
    extra_context: Optional[dict[str, Any]] = None,
    on_saved: Optional[Callable[[Any, Any], None]] = None,
    page_meta: Optional[dict[str, Any]] = None,
):
    """Create/update view shared by every admin entity form."""
    form = form_class(request.POST or None, request.FILES or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        obj = form.save()
        if on_saved:
            on_saved(obj, request)
        messages.success(request, success_message % getattr(obj, "__str__", obj))
        return redirect(success_url_name)
    context: dict[str, Any] = {"form": form, "instance": instance}
    if page_meta:
        context.update(page_meta)
    if extra_context:
        context.update(extra_context)
    return render(request, template_name, context)


@require_POST
def crud_delete(request, *, model, pk, success_url_name: str, success_message: str = "Deleted."):
    obj = get_object_or_404(model, pk=pk)
    label = str(obj)
    obj.delete()
    messages.success(request, success_message % label)
    return redirect(success_url_name)
