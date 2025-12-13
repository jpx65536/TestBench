from django.urls import path

from . import views

urlpatterns = [
    path("testcase/", views.testcase, name="testcase"),
    path("keyword/", views.keyword, name="keyword"),
    path("project/", views.project, name="project"),
    path("healthz/", views.healthz, name="healthz"),

    path("ui/project/", views.ui_project, name="ui_project"),
    path("ui/keyword/", views.ui_keyword, name="ui_keyword"),
    path("ui/testcase/", views.ui_testcase, name="ui_testcase"),
]