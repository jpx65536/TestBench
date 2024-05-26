import json

from django.shortcuts import render
from .models import Testcase
from django.http import HttpResponse, JsonResponse
from django.core.serializers import serialize

"""
{
    "operate": "create/update/delete/show_all/search",
    "parameters": {
        pass
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
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
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
    try:
        testcases = Testcase.objects.all()
    except Exception as e:
        print(f"except:{e}, type:{type(e)}")
    else:
        return testcases


def search_testcase(request):
    pass


def create_testcase(request):
    pass


def update_testcase(request):
    pass


def delete_testcase(request):
    pass
