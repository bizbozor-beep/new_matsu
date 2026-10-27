from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("matsu/", views.matsu, name="matsu"),
    path(
        "matsu/<int:pk>/edit/",
        views.edit_participant,
        name="edit_participant",
    ),
]