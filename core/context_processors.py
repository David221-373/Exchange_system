from core.models import LegalPage


def footer_legal_pages(request):
    try:
        pages = list(LegalPage.objects.all().order_by("sort_order", "title"))
    except Exception:
        pages = []
    return {"footer_legal_pages": pages}
