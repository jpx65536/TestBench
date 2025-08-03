import requests
import pytest
import logging
import json

logger = logging.getLogger(__name__)


def create_project(base_url, name, description):
    """
    创建项目，网络层断言后返回原始 response JSON。
    """
    url = f"{base_url}/testplatform/project/"
    payload = {
        "operate": "create",
        "parameters": {
            "name": name,
            "description": description
        }
    }
    resp = requests.post(url, json=payload, timeout=5)
    logger.info("Create project response: %s %s", resp.status_code, resp.text)
    assert resp.status_code == 200, f"创建项目 HTTP 失败: {resp.status_code}, body={resp.text}"
    try:
        data = resp.json()
    except ValueError:
        pytest.fail(f"创建项目返回不可解析 JSON: {resp.text}")
    return data

def delete_project(base_url, project_names):
    """
    删除项目（可能不存在），网络层断言后返回原始 response JSON。
    """
    url = f"{base_url}/testplatform/project/"
    payload = {
        "operate": "delete",
        "parameters": {
            "delete_list": project_names
        }
    }
    resp = requests.post(url, json=payload, timeout=5)
    logger.info("Delete project '%s' response: %s %s", project_names, resp.status_code, resp.text)
    assert resp.status_code == 200, f"删除项目 HTTP 失败: {resp.status_code}, body={resp.text}"
    try:
        data = resp.json()
    except ValueError:
        pytest.fail(f"删除项目返回不可解析 JSON: {resp.text}")
    return data

def update_project(base_url, new_name, new_description, source_name):
    """
    修改项目，网络层断言后返回原始 response JSON。
    """
    url = f"{base_url}/testplatform/project/"
    payload = {
        "operate": "update",
        "parameters": {
            "name": new_name,
            "description": new_description,
            "update_source_name": source_name
        }
    }
    resp = requests.post(url, json=payload, timeout=5)
    logger.info("Update project payload: %s", payload)
    logger.info("Update project response: %s %s", resp.status_code, resp.text)
    assert resp.status_code == 200, f"修改项目 HTTP 失败: {resp.status_code}, body={resp.text}"
    try:
        data = resp.json()
    except ValueError:
        pytest.fail(f"修改项目返回不可解析 JSON: {resp.text}")
    return data


def show_all_project(base_url):
    """
    展示所有项目，网络层断言后返回原始 response JSON。
    """
    url = f"{base_url}/testplatform/project/"
    payload = {
        "operate": "show_all",
        "parameters": {}
    }
    resp = requests.post(url, json=payload, timeout=5)
    logger.info("Show all projects response: %s %s", resp.status_code, resp.text)
    assert resp.status_code == 200, f"展示所有项目 HTTP 失败: {resp.status_code}, body={resp.text}"
    try:
        data = resp.json()
    except ValueError:
        pytest.fail(f"展示所有项目返回不可解析 JSON: {resp.text}")
    return data



@pytest.mark.usefixtures("wait_for_server")
def test_project_function(base_url):
    original_name = "Project A"
    original_desc = "Description for Project A"
    updated_name = "Project A_bak"
    updated_desc = "Description for Project A_bak"

    # 前置：删掉残留 original 和 updated（只打印，不断言）
    pre_orig = delete_project(base_url, [original_name])
    logger.info("[前置] original 删除返回: %s", json.dumps(pre_orig, ensure_ascii=False, indent=4))

    pre_updated = delete_project(base_url, [updated_name])
    logger.info("[前置] updated 删除返回: %s", json.dumps(pre_updated, ensure_ascii=False, indent=4))

    # 创建 original project A，并断言
    create_resp = create_project(base_url, original_name, original_desc)
    logger.info("[创建] 创建响应: %s", json.dumps(create_resp, ensure_ascii=False, indent=4))
    assert create_resp.get("code") == 200, f"创建项目业务 code 不是 200: {create_resp}"
    assert create_resp.get("message") == "create project success", f"创建项目 message 不对: {create_resp}"
    testcases = create_resp.get("testcases", [])
    assert testcases and isinstance(testcases, list), f"缺少 testcases: {create_resp}"
    fields = testcases[0].get("fields", {})
    assert fields.get("name") == original_name, f"创建后 name 错误: {fields}"
    assert fields.get("description") == original_desc, f"创建后 description 错误: {fields}"

    # 新增：展示所有项目，断言包含刚创建的 project A
    all_resp = show_all_project(base_url)
    logger.info("[展示] 展示所有项目响应: %s", json.dumps(all_resp, ensure_ascii=False, indent=4))
    assert all_resp.get("code") == 200, f"展示项目业务 code 不是 200: {all_resp}"
    assert all_resp.get("message") == "search all project successfully", f"展示所有项目 message 不对: {all_resp}"
    all_testcases = all_resp.get("testcases", [])
    assert isinstance(all_testcases, list) and all_testcases, f"展示所有项目缺少 testcases: {all_resp}"
    # 找到 name == original_name 的 entry 并验证 description
    matched = [
        tc for tc in all_testcases
        if tc.get("fields", {}).get("name") == original_name
    ]
    assert matched, f"展示结果中找不到创建的项目 {original_name}: {all_resp}"
    matched_fields = matched[0].get("fields", {})
    assert matched_fields.get("description") == original_desc, f"展示项目 description 不符: {matched_fields}"

    # 修改 original -> updated，并断言
    update_resp = update_project(base_url, updated_name, updated_desc, source_name=original_name)
    logger.info("[修改] 修改响应: %s", json.dumps(update_resp, ensure_ascii=False, indent=4))
    assert update_resp.get("code") == 200, f"修改项目业务 code 不是 200: {update_resp}"
    assert update_resp.get("message") == "update project success", f"修改项目 message 不对: {update_resp}"
    testcases = update_resp.get("testcases", [])
    assert testcases and isinstance(testcases, list), f"缺少 testcases: {update_resp}"
    fields = testcases[0].get("fields", {})
    assert fields.get("name") == updated_name, f"修改后 name 不对: {fields}"
    assert fields.get("description") == updated_desc, f"修改后 description 不对: {fields}"

    # 后置：删掉修改后的 updated（只打印返回，不断言）
    post_orig = delete_project(base_url, [original_name])
    logger.info("[后置] original 删除返回: %s", json.dumps(post_orig, ensure_ascii=False, indent=4))

    post_updated = delete_project(base_url, [updated_name])
    logger.info("[后置] updated 删除返回: %s", json.dumps(post_updated, ensure_ascii=False, indent=4))