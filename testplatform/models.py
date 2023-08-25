from django.db import models


# Create your models here.


class Testcase(models.Model):
    # name: 用例编号,字母+数字（唯一）； text：名称，中文+英文（唯一）； level：等级；
    testcase_name = models.CharField(max_length=50, unique=True)
    testcase_text = models.CharField(max_length=100, unique=True)
    testcase_level = models.IntegerField(default=0)

    def __str__(self):
        return self.testcase_text
