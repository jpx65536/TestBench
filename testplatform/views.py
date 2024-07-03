import json

from django.shortcuts import render
from .models import Testcase, KeyWord
from django.http import HttpResponse, JsonResponse
from django.core.serializers import serialize
from django.core.exceptions import ValidationError

"""
{
    "operate": "create/update/delete/show_all/search",
    "parameters": {
        "title": "title",
        "name": "name",
        "level": "level",
        "precondition": "precondition",
        "test_precondition": "test_precondition",
        "expected_result": "expected_result",
        "type": "type",
        "auto_flag": "auto_flag",
        "update_source_title": "update_source_title",
        "delete_title_list": []
    }
}
"""


def testcase(request):
    # create update delete show_all search
    if request.method == 'POST':
        try:
            print(request.body.decode('utf-8'))
            source_data = json.loads(request.body)
            operate = source_data["operate"]
            parameters = source_data["parameters"]
            if operate == "create":
                code = 200
                message = "create testcase success"
                testcases = create_testcase(parameters)
            elif operate == "update":
                code = 200
                message = "update testcase success"
                testcases = update_testcase(parameters)
            elif operate == "delete":
                code = 200
                message = "delete testcase success"
                testcases = delete_testcase(parameters)
            elif operate == "show_all":
                testcases = show_all_testcases(parameters)
                code = 200
                message = "search all testcases successfully"
            elif operate == "search":
                search_testcase(parameters)
        except Exception as e:
            print(f"except:{e}, type:{type(e)}")
            return JsonResponse({'error': f"except:{e}, type:{type(e)}"}, status=400)
        else:
            return JsonResponse(
                {
                    "code": code,
                    "message": message,
                    "testcases": serialize("json", testcases),
                },
                status=200
            )
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)


def show_all_testcases(parameters):
    testcases = Testcase.objects.all()
    return testcases


def search_testcase(parameters):
    pass


def create_testcase(parameters):
    new_testcase = Testcase(
        title=parameters["title"],
        name=parameters["name"],
        level=parameters["level"],
        precondition=parameters["precondition"],
        test_precondition=parameters["test_precondition"],
        expected_result=parameters["expected_result"],
        type=parameters["type"],
        auto_flag=parameters["auto_flag"]
    )
    new_testcase.save()
    new_testcase_query = Testcase.objects.filter(id=new_testcase.id)
    return new_testcase_query


def update_testcase(parameters):
    # 修改用例逻辑：用户操作，在用例展示界面，修改字段值，点击保存，即可修改
    # 接口逻辑：展示界面，会拿到用例所有字段信息，修改字段，请求过去即更改
    new_testcase = Testcase.objects.filter(title=parameters["update_source_title"]).first()
    if not new_testcase:
        raise ValidationError('Testcase not found')

    new_testcase.title = parameters.get("title", new_testcase.title)
    new_testcase.name = parameters.get("name", new_testcase.name)
    new_testcase.level = parameters.get("level", new_testcase.level)
    new_testcase.precondition = parameters.get("precondition", new_testcase.precondition)
    new_testcase.test_precondition = parameters.get("test_precondition", new_testcase.test_precondition)
    new_testcase.expected_result = parameters.get("expected_result", new_testcase.expected_result)
    new_testcase.type = parameters.get("type", new_testcase.type)
    new_testcase.auto_flag = parameters.get("auto_flag", new_testcase.auto_flag)

    new_testcase.full_clean()
    new_testcase.save()
    new_testcase_query = Testcase.objects.filter(id=new_testcase.id)
    return new_testcase_query


def delete_testcase(parameters):
    testcases_to_delete = Testcase.objects.filter(title__in=parameters["delete_title_list"])
    if not testcases_to_delete:
        raise ValidationError('No matching testcases found for delete')
    testcases_to_delete.delete()
    remaining_testcases = Testcase.objects.filter(title__in=parameters["delete_title_list"])
    return remaining_testcases


def keyword(request):
    if request.method == 'POST':
        try:
            print(request.body.decode('utf-8'))
            source_data = json.loads(request.body)
            operate = source_data["operate"]
            parameters = source_data["parameters"]
            if operate == "create":
                code = 200
                message = "create keyword success"
                keyword = create_keyword(parameters)
            elif operate == "update":
                code = 200
                message = "update keyword success"
                keyword = update_testcase(parameters)
            elif operate == "delete":
                code = 200
                message = "delete keyword success"
                keyword = delete_testcase(parameters)
            elif operate == "show_all":
                keyword = show_all_testcases(parameters)
                code = 200
                message = "search all keyword successfully"
            elif operate == "search":
                search_testcase(parameters)
        except Exception as e:
            print(f"except:{e}, type:{type(e)}")
            return JsonResponse({'error': f"except:{e}, type:{type(e)}"}, status=400)
        else:
            return JsonResponse(
                {
                    "code": code,
                    "message": message,
                    "testcases": serialize("json", keyword),
                },
                status=200
            )
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)


def create_keyword(parameters):
    required_fields = ['name', 'url', 'params', 'headers', 'body_type', 'body']
    for field in required_fields:
        if field not in parameters:
            raise ValidationError(f"Missing required field: {field}")
    new_keyword = KeyWord.objects.create(
        name=parameters['name'],
        url=parameters['url'],
        params=parameters['params'],
        headers=parameters['headers'],
        body_type=parameters['body_type'],
        body=parameters['body']
    )
    new_keyword.save()
    new_keyword_query = KeyWord.objects.filter(id=new_keyword.id)
    return new_keyword_query