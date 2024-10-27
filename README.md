# TestBench
接口自动化测试平台

testcase(文本)  
单个新增、  
单个修改、  
按照title查询、（单个、多个、0）如果是0，则要有不一样的message  
搜索全部（存在、一个用例也没有）  
删除多个（单个）  

keyword操作  
新增、修改、查询、删除  
请求结构
```
{
    "operate": "create/update/delete/show_all/search",
    "project_name": "projectA",
    "parameters": {
        "name": "Example API Request",
        "url": "https://example.com/api",
        "method": "GET",
        "params": {"param1": "value1", "param2": "value2"},
        "headers": {"Authorization": "Bearer token"},
        "body_type": "application/x-www-form-urlencoded",
        "body": "helloworld",
        "update_source_name": "update_source_name",
        "delete_name_list": [],
        "assertions": [
            {
                "target_value": "response_time",
                "operator": "less_than",
                "compared_value": "200"
            },
            {
                "target_value": "status_code",
                "operator": "equal",
                "compared_value": "200"
            }
        ]
    }
}
```
关键字：新增、修改等，默认是不填value的，当然，也可以填默认value，  
自动化用例，新增测试步骤=关键字+填补关键字的参数

业务逻辑设计：  
1、创建keyword：填入url、header等参数，设计出关键字，参数中value可以是默认，可以是空  
2、创建自动化用例，引入已有的关键字，并给关键字中的空值赋值，keyword按照给定顺序排序。  
3、执行用例，用例根据关键字+数据，一次发请求，获得结果，并校验。  
改进点：自动化用例，允许创建空的keyword，为所有选项填值。也就是keyword要允许为空。  

创建testcase的视图逻辑  
入参
```
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
                "body": "value1_body",
                "assertions": [
                    {
                        "target_value": "response_time",
                        "operator": "less_than",
                        "compared_value": "200"
                    },
                    {
                        "target_value": "status_code",
                        "operator": "equal",
                        "compared_value": "200"
                    }
                ]
            },
            {
                "name": "keyword2",
                "order": 2,
                "params": {"param1": "value2_param1", "param2": "value2_param2"},
                "headers": {"Authorization": "Bearer value2_token"},
                "body": "value2_body",
                "assertions": [
                    {
                        "target_value": "response_time",
                        "operator": "less_than",
                        "compared_value": "100"
                    }
                ]
            }
        ]
    }
}
```