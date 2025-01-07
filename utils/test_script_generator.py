import os
import json
import django
from django.core.exceptions import ValidationError

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TestBench.settings')  # 修改为您的 settings 模块路径
django.setup()

from testplatform.models import Project, Testcase, TestCaseKeyword, Assertion

def create_test_script(project_name, testcase_title):
    try:
        project = Project.objects.get(name=project_name)
    except Project.DoesNotExist:
        raise ValidationError(f"Project '{project_name}' not found")

    try:
        testcase = Testcase.objects.get(project=project, title=testcase_title)
    except Testcase.DoesNotExist:
        raise ValidationError(f"Testcase with title '{testcase_title}' not found in project '{project_name}'")

    testcase_keywords = TestCaseKeyword.objects.filter(test_case=testcase)
    steps = []
    for tk in testcase_keywords:
        assertions = Assertion.objects.filter(testcase_keyword=tk).values('target_value', 'operator', 'compared_value')
        steps.append({
            'url': tk.url,
            'method': tk.method,
            'params': tk.params,
            'headers': tk.headers,
            'body_type': tk.body_type,
            'body': tk.body,
            'assertions': list(assertions)
        })

    # 生成文件内容
    script_content = f"""
import requests
import json

def {project_name}_{testcase_title}():

"""
    for i, step in enumerate(steps, start=1):
        script_content += f"""
    # step{i}: 执行请求并验证断言
    url = "{step['url']}"
    method = "{step['method']}"
    params = {step['params']}
    headers = {step['headers']}
    body = {step['body']}
    response = requests.request(method, url, params=params, headers=headers, data=body if "{step['body_type']}" == "application/x-www-form-urlencoded" else json.dumps(body))

"""
        for assertion in step['assertions']:
            target_value = assertion['target_value']
            operator = assertion['operator']
            compared_value = assertion['compared_value']
            if operator == 'greater_than':
                script_content += f"    assert {target_value} > {compared_value}\n"
            elif operator == 'less_than':
                script_content += f"    assert {target_value} < {compared_value}\n"
            elif operator == 'equal':
                script_content += f"    assert {target_value} == {compared_value}\n"
            elif operator == 'greater_than_or_equal':
                script_content += f"    assert {target_value} >= {compared_value}\n"
            elif operator == 'less_than_or_equal':
                script_content += f"    assert {target_value} <= {compared_value}\n"
            elif operator == 'equal_to':
                script_content += f"    assert '{compared_value}' in {target_value}\n"
            elif operator == 'contains':
                script_content += f"    assert '{compared_value}' in {target_value}\n"
            elif operator == 'in':
                script_content += f"    assert {target_value} in '{compared_value}'\n"

    script_content += f"""
if __name__ == "__main__":
    {project_name}_{testcase_title}()
"""

    # 文件名
    file_name = f"{project_name}_{testcase_title}.py"
    # 上一级目录的casefile文件夹路径
    casefile_dir = os.path.join(os.path.dirname(os.getcwd()), 'casefile')
    # 确保casefile文件夹存在
    os.makedirs(casefile_dir, exist_ok=True)
    # 完整的文件路径
    file_path = os.path.join(casefile_dir, file_name)

    # 写入文件
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(script_content)

    print(f"Test script written to {file_path}")


if __name__ == '__main__':
    create_test_script(project_name="Project A", testcase_title="autocase0807_001")