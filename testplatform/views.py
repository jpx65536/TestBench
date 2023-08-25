from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from .models import Testcase
from .serializers import TestcaseModelSerializer


# Create your views here.

class TestcaseAPIView(ModelViewSet):
    queryset = Testcase.objects.all()
    serializer_class = TestcaseModelSerializer
