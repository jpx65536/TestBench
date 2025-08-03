from django.urls import path

from . import views

urlpatterns = [
    path("testcase/", views.testcase, name="testcase"),
    path("keyword/", views.keyword, name="keyword"),
    path("project/", views.project, name="project"),
    path("healthz/", views.healthz, name="healthz"),
]