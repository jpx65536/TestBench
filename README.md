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