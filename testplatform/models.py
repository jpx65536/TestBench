import functools
import uuid
import random
import string

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


# Create your models here.
def generate_random_string(except_str, length=10):
    characters = string.ascii_letters + string.digits
    random_chars = ''.join(random.choice(characters) for _ in range(length))
    return f'{except_str}_{random_chars}' if except_str else random_chars


def validate_positive(value):
    if value < 0:
        raise ValidationError('%(value)s is not a positive integer or 0', params={'value': value})


class Testcase(models.Model):
    # title：标题； name：编号； level：等级；前置条件，测试步骤，预期结果
    title_default = functools.partial(generate_random_string, "title")
    name_default = functools.partial(generate_random_string, "test")
    title = models.CharField(max_length=50, unique=True, null=False, blank=False, default=title_default)
    name = models.CharField(max_length=50, unique=True, null=False, blank=False, default=name_default)
    level = models.IntegerField(default=0, validators=[validate_positive])
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


class KeyWord(models.Model):
    BODY_TYPES = [
        ('application/x-www-form-urlencoded', 'Application/X-WWW-Form-Urlencoded'),
        ('raw', 'Raw'),
        ('multipart/form-data', 'Multipart/Form-Data'),
    ]
    name_default = functools.partial(generate_random_string, "kw")
    name = models.CharField(max_length=100, unique=True, null=False, blank=False, default=name_default)
    url = models.URLField()
    params = models.JSONField(blank=True, null=True)
    headers = models.JSONField(blank=True, null=True)
    body_type = models.CharField(max_length=50, choices=BODY_TYPES)
    body = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class AutoCase(models.Model):
    name = models.CharField(max_length=100)
    keywords = models.ManyToManyField(KeyWord, through='AutoCaseKeyword')

    def __str__(self):
        return self.name


class AutoCaseKeyword(models.Model):
    auto_case = models.ForeignKey(AutoCase, on_delete=models.CASCADE)
    keyword = models.ForeignKey(KeyWord, on_delete=models.CASCADE)
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.auto_case.name} - {self.keyword.name} ({self.order})"
