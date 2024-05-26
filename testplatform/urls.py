from django.urls import path

from . import views

urlpatterns = [
    path("testcase/", views.testcase, name="testcase"),
]