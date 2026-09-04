from django.urls import path
from . import views

urlpatterns = [
    path("health/", views.health),
    path("articles/", views.article_list, name="article-list"),
    path("articles/trending/", views.trending_articles, name="trending"),
    path("articles/bulk-view-increment/", views.bulk_view_increment, name="bulk-view-increment"),
    path("articles/<int:pk>/", views.article_detail, name="article-detail"),
]
