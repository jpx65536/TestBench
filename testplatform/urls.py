from .views import TestcaseAPIView
from rest_framework.routers import DefaultRouter

urlpatterns = []

router = DefaultRouter()
router.register("testcase", TestcaseAPIView)
urlpatterns += router.urls
