# TestBench
接口自动化测试平台

keyword操作
新增、修改、查询、删除
请求结构
{
    "operate": "create update delete show_all search",
    "parameters": {
        name='Example API Request',
        url='https://example.com/api',
        params={'param1': 'value1', 'param2': 'value2'},
        headers={'Authorization': 'Bearer token'},
        body_type='application/x-www-form-urlencoded',
        body='helloworld'
    }
}
关键字：新增、修改等，默认是不填value的，当然，也可以填默认value，
自动化用例，新增测试步骤=关键字+填补关键字的参数

业务逻辑设计：
1、创建keyword：填入url、header等参数，设计出关键字，参数中value可以是默认，可以是空
2、创建自动化用例，引入已有的关键字，并给关键字中的空值赋值，keyword按照给定顺序排序。
3、执行用例，用例根据关键字+数据，一次发请求，获得结果，并校验。
改进点：自动化用例，允许创建空的keyword，为所有选项填值。也就是keyword要允许为空。

创建autocase的视图逻辑
入参
{
    "operate": create delete update search
    "parameters": {
        "auto_case_name": "AutoCase 1",
        "keywords": [
            {
                "name": "Keyword 1",
                "order": 1,
                "params": {"param1": "value1_param1", "param2": "value1_param2"},
                "headers": {"Authorization": "Bearer value1_token"},
                "body": "value1_body"
            },
            {
                "name": "Keyword 2",
                "order": 2,
                "params": {"param1": "value2_param1", "param2": "value2_param2"},
                "headers": {"Authorization": "Bearer value2_token"},
                "body": "value2_body"
            }
        ]   
    }
}