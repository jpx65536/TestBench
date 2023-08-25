from rest_framework import serializers
from .models import Testcase


class TestcaseModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Testcase
        fields = "__all__"
