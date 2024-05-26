import json

from django.shortcuts import render
from .models import Testcase
from django.http import HttpResponse, JsonResponse
from django.core.serializers import serialize

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
        "auto_flag": "auto_flag"
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
                create_testcase(parameters)
            elif operate == "update":
                update_testcase(parameters)
            elif operate == "delete":
                delete_testcase(parameters)
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
    return new_testcase


def update_testcase(parameters):
    pass


def delete_testcase(parameters):
    pass
