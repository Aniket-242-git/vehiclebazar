"""Template context: expose the current modal offer site-wide (one query)."""
from apps.offers.services import OfferService


def active_offer(request):
    # Skip on admin panel pages to keep management screens clean.
    if request.path.startswith("/admin-panel/") or request.path.startswith("/django-admin/"):
        return {"modal_offer": None}
    return {"modal_offer": OfferService.get_modal_offer()}
