from django.http import HttpResponse, JsonResponse
from django.core.cache.utils import make_template_fragment_key
from django.conf import settings
from django.shortcuts import get_object_or_404, render
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_POST
from django.views.decorators.vary import vary_on_cookie

from .models import Article
from .services import get_trending_articles, get_trending_articles_unsafe, increment_all_view_counts


def health(request):
    return HttpResponse("ok")


@cache_page(60 * 15)
@vary_on_cookie
def article_list(request):
    return render(request, "news/article_list.html", {"articles": Article.objects.select_related("author").all()})


def trending_articles(request):
    getter = get_trending_articles_unsafe if settings.TRENDING_MODE == "unsafe" else get_trending_articles
    return JsonResponse({"articles": getter()})


@require_POST
def bulk_view_increment(request):
    increment_all_view_counts()
    return HttpResponse(status=204)


def article_detail(request, pk):
    article = get_object_or_404(Article, pk=pk)
    response = render(request, "news/article_detail.html", {"article": article})
    response["X-Fragment-Cache-Key"] = make_template_fragment_key(
        "article_body", [article.pk, article.updated_at.timestamp()]
    )
    return response
