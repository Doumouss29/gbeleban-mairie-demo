from django.shortcuts import get_object_or_404, render

from .models import News


def news_detail(request, news_id):
    news_item = get_object_or_404(News, pk=news_id, is_published=True)
    return render(request, "portal/news_detail.html", {"news_item": news_item})
