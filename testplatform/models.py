import uuid
import random
import string

from django.db import models


# Create your models here.
def generate_random_string(length):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

class Testcase(models.Model):
    # title：标题； name：编号； level：等级；前置条件，测试步骤，预期结果

    title = models.CharField(max_length=50, unique=True, null=False, blank=False, default=generate_random_string(10))
    name = models.CharField(max_length=50, unique=True, null=False, blank=False, default=generate_random_string(10))
    level = models.IntegerField(default=0)
    precondition = models.CharField(max_length=300, null=True, blank=True, default=None)
    test_precondition = models.CharField(max_length=300, null=True, blank=True, default=None)
    expected_result = models.CharField(max_length=300, null=True, blank=True, default=None)
    TYPE = [
        ("function_case", "功能用例"),
        ("performance_case", "性能用例"),
        ("reliability_case", "可靠性用例"),
    ]
    type = models.CharField(max_length=20, choices=TYPE, default="function_case")
    auto_flag = models.BooleanField(default=False, null=True, blank=True)

    def __str__(self):
        return f"{self.title}_{self.name}"
