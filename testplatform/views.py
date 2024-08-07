import json
import logging
import traceback

from django.shortcuts import render
from .models import Testcase, KeyWord, TestCaseKeyword, Project, Assertion
from django.http import HttpResponse, JsonResponse
from django.core.serializers import serialize
from django.core.exceptions import ValidationError
from django.db import transaction
from .serializers import ProjectSerializer

logger = logging.getLogger(__name__)

"""
{
    "operate": "create/update/delete/show_all/search",
    "project_name": "projectA",
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
        "delete_title_list": [],
        "description": "description",
        "keywords": [
            {
                "name": "Example API Request",
                "order": 1,
                "params": {"param1": "value1_param1", "param2": "value1_param2"},
                "headers": {"Authorization": "Bearer value1_token"},
                "body": "value1_body"
            },
            {
                "name": "kyeword2",
                "order": 2,
                "params": {"param1": "value2_param1", "param2": "value2_param2"},
                "headers": {"Authorization": "Bearer value2_token"},
                "body": "value2_body"
            }
        ]
    }
}
"""


def testcase(request):
    # create update delete show_all search
    if request.method == 'POST':
        try:
            logger.info(request.body.decode('utf-8'))
            source_data = json.loads(request.body)
            operate = source_data["operate"]
            project_name = source_data.get("project_name")
            parameters = source_data["parameters"]
            if operate == "create":
                code = 200
                message = "create testcase success"
                testcases = create_testcase(project_name, parameters)
            elif operate == "update":
                code = 200
                message = "update testcase success"
                testcases = update_testcase(project_name, parameters)
            elif operate == "delete":
                # delete逻辑正常，那么返回的testcases就为空，如果有值的话，这段逻辑就有问题了
                code = 200
                message = "delete testcase success"
                testcases = delete_testcase(project_name, parameters)
            elif operate == "show_all":
                testcases = show_all_testcases(project_name, parameters)
                code = 200
                message = "search all testcases successfully"
            elif operate == "search":
                testcases = search_testcase(project_name, parameters)
                code = 200
                if testcases is None:
                    message = "no testcases match"
                    testcases = []
                else:
                    message = "search testcases successfully"
            elif operate == "show_testcase":
                testcase, testcase_keywords, keyword_assertions = show_testcase(project_name, parameters)
                code = 200
                message = "show testcase successfully"
                testcase_data = json.loads(serialize("json", [testcase]))[0]
                testcase_keywords_data = json.loads(serialize("json", testcase_keywords))
                response_data = {
                    "code": code,
                    "message": message,
                    "testcase": testcase_data,
                    "testcase_keywords": testcase_keywords_data,
                    "keyword_assertions": keyword_assertions,
                }
                return JsonResponse(response_data, status=200)
            else:
                code = 400
                message = "Unsupported operation"
                return JsonResponse(
                    {
                        "code": code,
                        "message": message,
                    },
                    status=code
                )

        except Exception as e:
            logger.error(f"except:{e}, type:{type(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({'error': f"Exception: {e}, Type: {type(e)}, Traceback: {traceback.format_exc()}"}, status=400)
        else:
            # serialize函数:Django的serialize函数可以将QuerySet对象序列化为JSON格式，适合用于API响应。
            return JsonResponse(
                {
                    "code": code,
                    "message": message,
                    "testcases": json.loads(serialize("json", testcases)),
                },
                status=200
            )
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)


def show_all_testcases(project_name, parameters):
    # 应该要展示数量（可否由前端控制？）
    try:
        project = Project.objects.get(name=project_name)
    except Project.DoesNotExist:
        raise ValidationError(f"Project '{project_name}' not found")

    testcases = Testcase.objects.filter(project=project)
    return testcases


def search_testcase(project_name, parameters):
    # 前端只提供一个输入框，输入框的值只给了title，即按照title进行模糊搜索，传project name是默认的
    # 搜索成功，返回一个或多个用例；搜索失败
    title = parameters.get("title")

    if not project_name:
        raise ValidationError('Must provide project_name for searching')

    if not title:
        raise ValidationError('Must provide title for searching')

    # 查找匹配的项目
    try:
        project = Project.objects.get(name=project_name)
    except Project.DoesNotExist:
        raise ValidationError(f"Project '{project_name}' not found")

    # 生成 project_case 字段
    project_case = f"{project_name}_{title}"
    testcase_query = Testcase.objects.filter(project_case__icontains=project_case)
    if not testcase_query.exists():
        return None
    return testcase_query


def create_testcase(project_name, parameters):
    required_fields = ['title', 'name', 'level', 'precondition', 'test_precondition', 'expected_result', 'type', 'auto_flag', 'description', 'keywords']
    for field in required_fields:
        if field not in parameters:
            raise ValidationError(f"Missing required field: {field}")

    # 查找匹配的项目
    try:
        project = Project.objects.get(name=project_name)
    except Project.DoesNotExist:
        raise ValidationError(f"Project '{project_name}' not found")

    # transaction.atomic() 创建了一个原子事务块。块内的所有操作要么全部成功，要么全部失败。如果在事务块内引发异常（例如，如果未找到关键字），则事务将回滚，并且不会保存任何更改。
    # 这确保了 Testcase 和 TestCaseKeyword 对象的创建是原子的，要么全部完成，要么全部不完成。
    with transaction.atomic():
        new_testcase = Testcase(
            project=project,
            title=parameters["title"],
            name=parameters["name"],
            level=parameters["level"],
            precondition=parameters["precondition"],
            test_precondition=parameters["test_precondition"],
            expected_result=parameters["expected_result"],
            type=parameters["type"],
            auto_flag=parameters["auto_flag"],
            description=parameters.get('description', '')
        )
        new_testcase.save()

        # 处理关键字
        keywords_data = parameters.get('keywords', [])
        for keyword_data in keywords_data:
            keyword_name = keyword_data['name']
            order = keyword_data['order']
            params = keyword_data.get('params', {})
            headers = keyword_data.get('headers', {})
            body = keyword_data.get('body', '')
            url = keyword_data.get('url', '')
            method = keyword_data.get('method', '')
            body_type = keyword_data.get('body_type', '')
            # 查找匹配的 keyword
            try:
                this_keyword = KeyWord.objects.get(name=keyword_name)
            except KeyWord.DoesNotExist:
                raise ValidationError(f"没匹配到合适的keyword: {keyword_name}")

            testcase_keyword = TestCaseKeyword.objects.create(
                test_case=new_testcase,
                keyword=this_keyword,
                order=order,
                url=url,
                method=method,
                params=params,
                headers=headers,
                body_type=body_type,
                body=body
            )
            # 处理断言，此时断言要增加被比较值，
            assertions_data = keyword_data.get('assertions', [])
            for assertion_data in assertions_data:
                target_value = assertion_data.get('target_value')
                operator = assertion_data.get('operator')
                compared_value = assertion_data.get('compared_value')
                if not target_value or not operator or compared_value is None:
                    raise ValidationError(
                        "All of 'target_value', 'operator' and 'compared_value' are required and cannot be empty for each assertion")

                Assertion.objects.create(
                    target_value=target_value,
                    operator=operator,
                    compared_value=compared_value,
                    testcase_keyword=testcase_keyword
                )

    new_testcase_query = Testcase.objects.filter(id=new_testcase.id)
    return new_testcase_query


def update_testcase(project_name, parameters):
    # 修改用例逻辑：用户操作，在用例展示界面，修改字段值，点击保存，即可修改
    # 接口逻辑：展示界面，会拿到用例所有字段信息，修改字段，请求过去即更改
    # 前端用例界面进行修改，用例原标题用缓存先保留，发生update事件后，传值update_source_title，project字段由当前用例所属project赋值
    try:
        project = Project.objects.get(name=project_name)
    except Project.DoesNotExist:
        raise ValidationError(f"Project '{project_name}' not found")

    try:
        new_testcase = Testcase.objects.get(project=project, title=parameters["update_source_title"])
    except Testcase.DoesNotExist:
        raise ValidationError('Testcase not found')
    with transaction.atomic():
        new_testcase.title = parameters.get("title", new_testcase.title)
        new_testcase.name = parameters.get("name", new_testcase.name)
        new_testcase.level = parameters.get("level", new_testcase.level)
        new_testcase.precondition = parameters.get("precondition", new_testcase.precondition)
        new_testcase.test_precondition = parameters.get("test_precondition", new_testcase.test_precondition)
        new_testcase.expected_result = parameters.get("expected_result", new_testcase.expected_result)
        new_testcase.type = parameters.get("type", new_testcase.type)
        new_testcase.auto_flag = parameters.get("auto_flag", new_testcase.auto_flag)
        new_testcase.description = parameters.get("description", new_testcase.description)

        # keyword逻辑改动比较麻烦，考虑前端必传keyword，不必判空（前端的update操作）
        # 前端的业务：用拖动、或者点击选中，从keyword目录引入一个keyword，并在前端进行排序
        # 以 (name, order) 为唯一的比较对象，来设计自动化用例的keyword更新逻辑：
        # 以请求中的 keyword 的 name - order为蓝本，按 name - order 向原始数据进行比较。
        # 如果原始数据中有相同的name - order，则比较其值，判断是否需要修改；如果原始数据中没有这个
        # name - order，则写入；如果原始数据中存在但请求中没有，则删除这个 name - order。
        # 前端要对传入keyword进行负责：首先是排序，order不能乱，必须要连续；其次保证格式，这个由前端组成来控制，后端只校验keyword是否存在
        keywords_data = parameters['keywords']
        current_keywords = list(
            TestCaseKeyword.objects.filter(test_case=new_testcase).values('keyword__name', 'order', 'params', 'headers',
                                                                          'body', 'url', 'body_type', 'method'))
        # 创建当前关键字数据字典
        current_keywords_dict = {}
        for keyword in current_keywords:
            key = (keyword['keyword__name'], keyword['order'])
            current_keywords_dict[key] = {
                'params': keyword['params'],
                'headers': keyword['headers'],
                'body': keyword['body'],
                'url': keyword['url'],
                'method': keyword['method'],
                'body_type': keyword['body_type']
            }

        # 创建请求关键字数据字典
        request_keywords_dict = {}
        for keyword_data in keywords_data:
            key = (keyword_data['name'], keyword_data['order'])
            request_keywords_dict[key] = {
                'params': keyword_data.get('params', {}),
                'headers': keyword_data.get('headers', {}),
                'body': keyword_data.get('body', ''),
                'url': keyword_data.get('url', ''),
                'method': keyword_data.get('method', ''),
                'body_type': keyword_data.get('body_type', ''),
                'assertions': keyword_data.get('assertions', [])
            }

        # 比较请求中的关键字与当前关键字，找出新增或修改的关键字（先找，而不是进行修改，避免影响到找这个步骤）
        to_delete_keywords = []
        to_add_or_update_keywords = []
        unchanged_keywords = []

        for key in current_keywords_dict:
            if key not in request_keywords_dict:
                to_delete_keywords.append(key)

        for key, value in request_keywords_dict.items():
            if key not in current_keywords_dict or current_keywords_dict[key] != value:
                to_add_or_update_keywords.append((key, value))
            else:
                unchanged_keywords.append(key)


            # 删除不存在的关键字关联
        for keyword, order in to_delete_keywords:
            TestCaseKeyword.objects.filter(test_case=new_testcase, keyword__name=keyword, order=order).delete()

        # 添加或更新关键字
        for (keyword_name, order), value in to_add_or_update_keywords:
            params = value['params']
            headers = value['headers']
            body = value['body']
            url = value['url']
            method = value['method']
            body_type = value['body_type']
            try:
                # 查找匹配的 keyword
                this_keyword = KeyWord.objects.get(name=keyword_name)
            except KeyWord.DoesNotExist:
                raise ValidationError(f"没匹配到合适的keyword: {keyword_name}")

            testcase_keyword, created = TestCaseKeyword.objects.update_or_create(
                test_case=new_testcase,
                keyword=this_keyword,
                order=order,
                defaults={
                    'params': params,
                    'headers': headers,
                    'body': body,
                    'body_type': body_type,
                    'url': url,
                    'method': method
                }
            )

            # 处理断言
            testcase_keyword.assertions.all().delete()
            assertions_data = value.get('assertions', [])
            for assertion_data in assertions_data:
                target_value = assertion_data.get('target_value')
                operator = assertion_data.get('operator')
                compared_value = assertion_data.get('compared_value')
                if not target_value or not operator or compared_value is None:
                    raise ValidationError(
                        "All of 'target_value', 'operator' and 'compared_value' are required and cannot be empty for each assertion")
                Assertion.objects.create(
                    target_value=target_value,
                    operator=operator,
                    compared_value=compared_value,
                    testcase_keyword=testcase_keyword
                )
        # 刷新未改动关键字的断言
        print('Unchanged keywords: {}'.format(unchanged_keywords))
        for keyword_name, order in unchanged_keywords:
            testcase_keyword = TestCaseKeyword.objects.get(test_case=new_testcase, keyword__name=keyword_name, order=order)
            testcase_keyword.assertions.all().delete()

            assertions_data = request_keywords_dict[(keyword_name, order)].get('assertions', [])
            for assertion_data in assertions_data:
                target_value = assertion_data.get('target_value')
                operator = assertion_data.get('operator')
                compared_value = assertion_data.get('compared_value')
                if not target_value or not operator or compared_value is None:
                    raise ValidationError(
                        "All of 'target_value', 'operator' and 'compared_value' are required and cannot be empty for each assertion")
                Assertion.objects.create(
                    target_value=target_value,
                    operator=operator,
                    compared_value=compared_value,
                    testcase_keyword=testcase_keyword
                )

        # 验证每个字段的值是否符合该字段的验证规则
        new_testcase.full_clean()
        new_testcase.save()

    new_testcase_query = Testcase.objects.filter(id=new_testcase.id)
    return new_testcase_query


def delete_testcase(project_name, parameters):
    # 在 TestCaseKeyword 模型中已经设置了 on_delete=models.CASCADE，
    # 当删除 Testcase 对象时，所有与之关联的 TestCaseKeyword 对象将会被自动删除。
    # 查找指定项目
    try:
        project = Project.objects.get(name=project_name)
    except Project.DoesNotExist:
        raise ValidationError(f"Project '{project_name}' not found")

    # 验证删除列表是否提供
    delete_title_list = parameters.get("delete_title_list", [])
    if not delete_title_list:
        raise ValidationError('Must provide delete_title_list for deletion')

    testcases_to_delete = Testcase.objects.filter(project=project, title__in=parameters["delete_title_list"])
    if not testcases_to_delete:
        raise ValidationError('No matching testcases found for delete')
    testcases_to_delete.delete()
    remaining_testcases = Testcase.objects.filter(title__in=parameters["delete_title_list"])
    return remaining_testcases


def show_testcase(project_name, parameters):
    title = parameters.get("title")
    if not title:
        raise ValidationError("Title must be provided for show_case operation")

    try:
        project = Project.objects.get(name=project_name)
    except Project.DoesNotExist:
        raise ValidationError(f"Project '{project_name}' not found")
    project_case = f"{project_name}_{title}"

    try:
        testcase = Testcase.objects.get(project_case=project_case)
    except Testcase.DoesNotExist:
        raise ValidationError(f"Testcase with project_case '{project_case}' not found")

    testcase_keywords = TestCaseKeyword.objects.filter(test_case=testcase)

    keyword_assertions = []
    for tk in testcase_keywords:
        assertions = Assertion.objects.filter(testcase_keyword=tk).values('id', 'keyword_id', 'testcase_keyword_id', 'target_value', 'operator', 'compared_value')
        keyword_assertions.extend(list(assertions))

    return testcase, testcase_keywords, keyword_assertions


def keyword(request):
    if request.method == 'POST':
        try:
            print(request.body.decode('utf-8'))
            source_data = json.loads(request.body)
            operate = source_data["operate"]
            parameters = source_data["parameters"]
            project_name = source_data.get("project_name")
            if operate == "create":
                code = 200
                message = "create keyword success"
                keywords = create_keyword(project_name, parameters)
            elif operate == "update":
                code = 200
                message = "update keyword success"
                keywords = update_keyword(project_name, parameters)
            elif operate == "delete":
                code = 200
                message = "delete keyword success"
                keywords = delete_keyword(project_name, parameters)
            elif operate == "show_all":
                keywords = show_all_keyword(project_name, parameters)
                code = 200
                message = "search all keyword successfully"
            elif operate == "search":
                keywords = search_keyword(project_name, parameters)
                code = 200
                if keywords is None:
                    message = "no keywords match"
                    keywords = []
                else:
                    message = "search keywords successfully"
            else:
                code = 400
                message = "Unsupported operation"
                return JsonResponse({"code": code, "message": message}, status=code)
        except Exception as e:
            print(f"except:{e}, type:{type(e)}")
            return JsonResponse({'error': f"except:{e}, type:{type(e)}"}, status=400)
        else:
            # serialize返回的字符串是json数组，所以再通过json.loads转换
            return JsonResponse(
                {
                    "code": code,
                    "message": message,
                    "keyword": json.loads(serialize("json", keywords)),
                },
                status=200
            )
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)


def create_keyword(project_name, parameters):
    # 校验字段完整性，然后直接赋值
    required_fields = ['name', 'url', 'params', 'headers', 'body_type', 'body', 'method']
    for field in required_fields:
        if field not in parameters:
            raise ValidationError(f"Missing required field: {field}")

    try:
        project = Project.objects.get(name=project_name)
    except Project.DoesNotExist:
        raise ValidationError(f"Project '{project_name}' not found")

    with transaction.atomic():
        # 设置关键字
        new_keyword = KeyWord.objects.create(
            name=parameters['name'],
            project=project,
            url=parameters['url'],
            method=parameters['method'],
            params=parameters['params'],
            headers=parameters['headers'],
            body_type=parameters['body_type'],
            body=parameters['body']
        )
        # 设置断言
        assertions_data = parameters.get('assertions', [])
        for assertion_data in assertions_data:
            target_value = assertion_data.get('target_value')
            operator = assertion_data.get('operator')
            if not target_value or not operator:
                raise ValidationError("Both 'target_value' and 'operator' are required and cannot be empty for each assertion")

            compared_value = assertion_data.get('compared_value')

            Assertion.objects.create(
                target_value=target_value,
                operator=operator,
                compared_value=compared_value,
                keyword=new_keyword
            )

        new_keyword_query = KeyWord.objects.filter(id=new_keyword.id)
    return new_keyword_query


def update_keyword(project_name, parameters):
    # 修改是针对已有的keyword进行修改，先根据源信息找到要修改的对象new_keyword
    # name为空，即修改本keyword；name不为空，则是要把本keyword的name修改掉
    try:
        project = Project.objects.get(name=project_name)
    except Project.DoesNotExist:
        raise ValidationError(f"Project '{project_name}' not found")

    new_keyword = KeyWord.objects.filter(project=project, name=parameters['update_source_name']).first()
    if not new_keyword:
        raise ValidationError("Keyword not found")

    new_keyword.name = parameters.get("name", new_keyword.name)
    new_keyword.url = parameters.get("url", new_keyword.url)
    new_keyword.method = parameters.get("method", new_keyword.method)
    new_keyword.params = parameters.get("params", new_keyword.params)
    new_keyword.body_type = parameters.get("body_type", new_keyword.body_type)
    new_keyword.headers = parameters.get("headers", new_keyword.headers)
    new_keyword.body = parameters.get("body", new_keyword.body)

    new_keyword.full_clean()
    new_keyword.save()

    # 处理断言
    assertions_data = parameters.get('assertions', [])
    if assertions_data:
        # 清除现有的断言，然后每个断言重新配置一遍
        new_keyword.assertions.all().delete()
        for assertion_data in assertions_data:
            target_value = assertion_data.get('target_value')
            operator = assertion_data.get('operator')
            if not target_value or not operator:
                raise ValidationError(
                    "Both 'target_value' and 'operator' are required and cannot be empty for each assertion")

            compared_value = assertion_data.get('compared_value', None)

            Assertion.objects.create(
                target_value=target_value,
                operator=operator,
                compared_value=compared_value,
                keyword=new_keyword
            )

    new_keyword_query = KeyWord.objects.filter(id=new_keyword.id)
    return new_keyword_query


def delete_keyword(project_name, parameters):
    # delete操作，暂时对齐前端勾选逻辑
    try:
        project = Project.objects.get(name=project_name)
    except Project.DoesNotExist:
        raise ValidationError(f"Project '{project_name}' not found")

    delete_name_list = parameters.get('delete_name_list', [])
    for name in delete_name_list:
        if not KeyWord.objects.filter(name=name).exists():
            logger.info(f"Keyword '{name}' not found in the database")
    keyword_to_delete = KeyWord.objects.filter(project=project, name__in=parameters['delete_name_list'])
    if not keyword_to_delete.exists():
        raise ValidationError("No matching keywords found for delete")
    keyword_to_delete.delete()
    remaining_keywords = KeyWord.objects.filter(name__in=parameters['delete_name_list'])
    return remaining_keywords


def show_all_keyword(project_name, parameters):
    try:
        project = Project.objects.get(name=project_name)
    except Project.DoesNotExist:
        raise ValidationError(f"Project '{project_name}' not found")
    return KeyWord.objects.filter(project=project)


def search_keyword(project_name, parameters):
    try:
        project = Project.objects.get(name=project_name)
    except Project.DoesNotExist:
        raise ValidationError(f"Project '{project_name}' not found")

    name = parameters.get("name")
    if not name:
        raise ValidationError('Must provide keyword name for searching')
    keywords = KeyWord.objects.filter(project=project, name__icontains=name)
    if not keywords.exists():
        return None  # 返回 None 表示没有找到对应的关键字
    return keywords


"""
project的创建、修改、删除、展示方法
{
    "operate": "create/update/delete/show_all",
    "parameters": {
        "name":
        "description"
        "update_source_name": "update_source_title",
        "delete_list": [],
    }
}"""
def project(request):
    # create update delete show_all search
    if request.method == 'POST':
        try:
            logger.info(request.body.decode('utf-8'))
            source_data = json.loads(request.body)
            operate = source_data["operate"]
            parameters = source_data["parameters"]
            if operate == "create":
                code, message, projects = create_project(parameters)
            elif operate == "update":
                code, message, projects = update_project(parameters)
            elif operate == "delete":
                code, message, projects = delete_project(parameters)
            elif operate == "show_all":
                code, message, projects = show_all_project(parameters)
            else:
                code = 400
                message = "Unsupported operation"
                return JsonResponse(
                    {
                        "code": code,
                        "message": message,
                    },
                    status=code
                )
        except Exception as e:
            logger.info(f"except:{e}, type:{type(e)}")
            return JsonResponse({'error': f"except:{e}, type:{type(e)}"}, status=400)
        else:
        # serialize函数:Django的serialize函数可以将QuerySet对象序列化为JSON格式，适合用于API响应。
            return JsonResponse(
                {
                    "code": code,
                    "message": message,
                    "testcases": json.loads(serialize("json", projects)),
                },
                status=200
            )

    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)


def create_project(parameters):
    serializer = ProjectSerializer(data=parameters)
    if serializer.is_valid():
        serializer.save()
        return 200, "create project success", Project.objects.filter(id=serializer.instance.id)
    return 400, serializer.errors, []


def update_project(parameters):
    try:
        # 使用 update_source_name 字段查找项目
        project = Project.objects.get(name=parameters["update_source_name"])
    except Project.DoesNotExist:
        return 404, "Project not found", []
    update_data = {k: v for k, v in parameters.items() if k in ["name", "description"]}
    serializer = ProjectSerializer(project, data=update_data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return 200, "update project success", Project.objects.filter(id=serializer.instance.id)
    return 400, serializer.errors, []


def delete_project(parameters):
    # list列表部分project存在，部分不存在，当作删除成功。因为不存在的项目是否删除都那个样。只要能删掉某个即可
    delete_list = parameters.get('delete_list', [])
    if not delete_list:
        return 400, "Project names are required for deletion", []

    deleted_projects = []
    failed_to_delete_projects = []

    for name in delete_list:
        try:
            # 检查项目是否包含自动化用例，虽然级联了用例表，但这样操作，可以减少数据库操作，不是依赖数据库级联删除
            project = Project.objects.get(name=name)
            if Testcase.objects.filter(project=project).exists():
                failed_to_delete_projects.append(name)
                logger.info(f"Project '{name}' has automated test cases and cannot be deleted")
            else:
                project.delete()
                deleted_projects.append(project)
        except Project.DoesNotExist:
            logger.info(f"Project '{name}' not found")

    if deleted_projects:
        return 200, "delete project success", []
    return 404, "No projects found to delete", []


def show_all_project(parameters):
    projects = Project.objects.all()
    return 200, "search all project successfully", projects
