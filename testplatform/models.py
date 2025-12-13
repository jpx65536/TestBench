import functools
import uuid
import random
import string

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


def generate_random_string(except_str, length=10):
    characters = string.ascii_letters + string.digits
    random_chars = ''.join(random.choice(characters) for _ in range(length))
    return f'{except_str}_{random_chars}' if except_str else random_chars


def validate_positive(value):
    if value < 0:
        raise ValidationError('%(value)s is not a positive integer or 0', params={'value': value})


class Project(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Testcase(models.Model):
    # 通过 related_name 访问所有关联的 Testcase 实例：testcases = project.testcases.all()
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='testcases')
    title_default = functools.partial(generate_random_string, "title")
    name_default = functools.partial(generate_random_string, "test")
    title = models.CharField(max_length=50, null=False, blank=False, default=title_default)
    name = models.CharField(max_length=50, null=False, blank=False, default=name_default)
    project_case = models.CharField(max_length=150, unique=True, null=False, blank=False)
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
    description = models.TextField(blank=True, null=True)
    keywords = models.ManyToManyField("KeyWord", through='TestCaseKeyword')

    class Meta:
        # unique_together 确保在数据库层面上字段组合的唯一性约束。在 Testcase 模型中，它确保每个项目中的 title 和 name 的组合是唯一的
        # 可以在数据库层面上提供额外的安全保障
        unique_together = ('project', 'title', 'name')

    def save(self, *args, **kwargs):
        # 在保存对象到数据库之前或之后执行一些操作。在 Testcase 模型中，重写了 save 方法以自动生成 project_case 字段的值
        self.project_case = f"{self.project.name}_{self.title}"
        super(Testcase, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.title}_{self.name}"


class KeyWord(models.Model):
    BODY_TYPES = [
        ('application/x-www-form-urlencoded', 'Application/X-WWW-Form-Urlencoded'),
        ('raw', 'Raw'),
        ('multipart/form-data', 'Multipart/Form-Data'),
    ]
    METHODS = [
        ('POST', 'POST'),
        ('GET', 'GET'),
        ('DELETE', 'DELETE'),
        ('PUT', 'PUT'),
    ]
    name_default = functools.partial(generate_random_string, "kw")
    name = models.CharField(max_length=100, null=False, blank=False, default=name_default)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='keywords')
    project_keyword = models.CharField(max_length=150, unique=True, null=False, blank=False)
    url = models.URLField()
    method = models.CharField(max_length=10, choices=METHODS, default='POST')
    params = models.JSONField(blank=True, null=True)
    headers = models.JSONField(blank=True, null=True)
    body_type = models.CharField(max_length=50, choices=BODY_TYPES)
    body = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('project', 'name')

    def save(self, *args, **kwargs):
        self.project_keyword = f"{self.project.name}_{self.name}"
        super(KeyWord, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


class TestCaseKeyword(models.Model):
    BODY_TYPES = [
        ('application/x-www-form-urlencoded', 'Application/X-WWW-Form-Urlencoded'),
        ('raw', 'Raw'),
        ('multipart/form-data', 'Multipart/Form-Data'),
    ]
    METHODS = [
        ('POST', 'POST'),
        ('GET', 'GET'),
        ('DELETE', 'DELETE'),
        ('PUT', 'PUT'),
    ]
    test_case = models.ForeignKey(Testcase, on_delete=models.CASCADE)
    keyword = models.ForeignKey(KeyWord, on_delete=models.CASCADE)
    order = models.PositiveIntegerField()
    url = models.URLField()
    method = models.CharField(max_length=10, choices=METHODS, default='POST')
    params = models.JSONField(blank=True, null=True)
    headers = models.JSONField(blank=True, null=True)
    body_type = models.CharField(max_length=50, choices=BODY_TYPES)
    body = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.test_case.name} - {self.keyword.name} ({self.order})"


class Assertion(models.Model):
    COMPARISON_OPERATORS = [
        ('greater_than', '大于'),
        ('less_than', '小于'),
        ('equal', '等于'),
        ('greater_than_or_equal', '大于等于'),
        ('less_than_or_equal', '小于等于'),
        ('equal_to', '相等'),
        ('contains', '包含'),
        ('in', '被包含'),
    ]

    target_value = models.CharField(max_length=255)
    operator = models.CharField(max_length=30, choices=COMPARISON_OPERATORS)
    compared_value = models.CharField(max_length=255, blank=True, null=True)
    keyword = models.ForeignKey(KeyWord, on_delete=models.CASCADE, related_name='assertions', null=True, blank=True)
    testcase_keyword = models.ForeignKey('TestCaseKeyword', on_delete=models.CASCADE, related_name='assertions', null=True, blank=True)

    def clean(self):
        # 保证至少有一个外键关联上，在模型实例保存之前执行自定义验证逻辑。使用 clean 方法，可以确保模型实例在保存到数据库之前符合特定的业务规则和逻辑约束。
        if not self.keyword and not self.testcase_keyword:
            raise ValidationError("Either 'keyword' or 'testcase_keyword' must be set.")

    def __str__(self):
        return f"{self.target_value} {self.operator} {self.compared_value or ''}"