# test_script_generator.py
import os
import re
import sys
import ast
import json
from pathlib import Path

import django
from django.core.exceptions import ValidationError

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "TestBench.settings")

import django
django.setup()

from testplatform.models import Project, Testcase, TestCaseKeyword, Assertion


# ===================== 工具：命名清洗 =====================
def _safe_fs_name(s: str) -> str:
    """用于文件/目录名：保留中英文、数字、下划线、短横线；其余替换成下划线。"""
    s = (s or "").strip()
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[^0-9A-Za-z_\-\u4e00-\u9fff]+", "_", s)
    return s.strip("_") or "unnamed"


def _safe_py_ident(s: str) -> str:
    """用于 Python 标识符片段（函数名）：只保留字母数字下划线，且不能以数字开头。"""
    s = (s or "").strip()
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[^0-9A-Za-z_]+", "_", s)
    s = s.strip("_") or "unnamed"
    if re.match(r"^\d", s):
        s = f"p_{s}"
    return s


# ===================== 工具：生成序号 0001（按项目目录下现有文件递增） =====================
def _next_seq_num(project_dir: Path) -> str:
    """
    在 casefile/{project}/ 下扫描 test_{project}_NNNN_*.py，取最大 NNNN + 1
    """
    max_n = 0
    if project_dir.exists():
        for p in project_dir.glob("test_*_????_*.py"):
            m = re.search(r"_([0-9]{4})_", p.name)
            if m:
                max_n = max(max_n, int(m.group(1)))
    return f"{max_n + 1:04d}"


# ===================== 工具：body 解析（只在生成器里做，生成文件里不出现） =====================
def _parse_body_text(body_text: str):
    """
    KeyWord/TestCaseKeyword.body 是 TextField。
    - 支持 Python dict 风格字符串（单引号）: ast.literal_eval
    - 支持 JSON 字符串: json.loads
    """
    if body_text is None:
        return None

    s = str(body_text).strip()
    if not s:
        return None

    # 先试 JSON
    try:
        return json.loads(s)
    except Exception:
        pass

    # 再试 Python 字面量
    try:
        return ast.literal_eval(s)
    except Exception:
        # 最差返回原字符串，生成到 data/json 时按字符串处理
        return s


# ===================== DSL → Python 表达式（生成期编译） =====================
def compile_target_value(target_value: str) -> str:
    """
    把 Assertion.target_value (DSL) 编译成 Python 表达式字符串（在生成期完成）
    仅支持：
      ${response}.code
      ${response}.body...
      ${response}.headers...
    """
    if not isinstance(target_value, str):
        raise ValueError(f"target_value must be str, got {type(target_value)}")

    tv = target_value.strip()
    prefix = "${response}."
    if not tv.startswith(prefix):
        raise ValueError(f"Unsupported target_value (must start with {prefix}): {tv}")

    expr = tv[len(prefix):]  # e.g. "code" / "body['message']" / "headers['X']"

    if expr == "code":
        return "resp.status_code"

    if expr.startswith("body"):
        # body -> resp.json() + 其余索引片段
        return "resp.json()" + expr[len("body"):]  # 保留后缀如 ['k']

    if expr.startswith("headers"):
        return "resp.headers" + expr[len("headers"):]  # 保留后缀如 ['k']

    raise ValueError(f"Unsupported response expression: {tv}")


# ===================== operator → assert 语句（生成期编译） =====================
def compile_assertion_line(target_expr_py: str, operator: str, compared_value: str) -> str:
    """
    根据你 V1 规则生成“纯 Python assert 语句”（生成文件里不需要任何 helper）
    数字类：greater_than / less_than / equal
    字符串类：equal_to / contains
    """
    op = (operator or "").strip()

    if op in ("greater_than", "less_than", "equal"):
        # 数字：把 compared_value 编译成数值字面量（int/float）
        s = str(compared_value).strip() if compared_value is not None else ""
        if s == "":
            raise ValueError(f"Numeric operator {op} requires compared_value")
        # 尽量 int，否则 float
        try:
            if re.fullmatch(r"-?\d+", s):
                num_lit = str(int(s))
            else:
                num_lit = str(float(s))
        except Exception:
            raise ValueError(f"compared_value is not a number for {op}: {compared_value}")

        sym = { "greater_than": ">", "less_than": "<", "equal": "==" }[op]
        return f"assert {target_expr_py} {sym} {num_lit}"

    if op in ("equal_to", "contains"):
        # 字符串：用 repr 做安全转义
        s = "" if compared_value is None else str(compared_value)
        lit = repr(s)
        if op == "equal_to":
            return f"assert {target_expr_py} == {lit}"
        else:
            return f"assert {lit} in {target_expr_py}"

    raise ValueError(f"Unsupported operator: {operator}")


# ===================== 生成 test 文件内容 =====================
def build_test_file_content(project_name: str, seq: str, testcase_name: str, steps: list[dict]) -> str:
    proj_ident = _safe_py_ident(project_name)
    case_ident = _safe_py_ident(testcase_name)
    func_name = f"test_{proj_ident}_{seq}_{case_ident}"

    lines: list[str] = []
    lines.append("import requests")
    lines.append("")
    lines.append("")
    lines.append("def send_request(url, method, headers=None, params=None, json_body=None, data_body=None, timeout=10):")
    lines.append("    return requests.request(")
    lines.append("        method=method,")
    lines.append("        url=url,")
    lines.append("        headers=headers,")
    lines.append("        params=params,")
    lines.append("        json=json_body,")
    lines.append("        data=data_body,")
    lines.append("        timeout=timeout,")
    lines.append("    )")
    lines.append("")
    lines.append("")
    lines.append(f"def {func_name}():")
    lines.append(f"    # project: {project_name}")
    lines.append(f"    # testcase: {testcase_name}")
    lines.append("")

    for idx, step in enumerate(steps, start=1):
        lines.append(f"    # ---------------- Step {idx} ----------------")
        lines.append(f"    url = {repr(step['url'])}")
        lines.append(f"    method = {repr(step['method'])}")
        lines.append(f"    params = {repr(step.get('params') or {})}")
        lines.append(f"    headers = {repr(step.get('headers') or {})}")

        body_type = step.get("body_type")
        body_val = step.get("body_value")

        # V1：raw 认为是 json_body；x-www-form-urlencoded 认为 data_body
        if body_type == "application/x-www-form-urlencoded":
            # form 表单
            if isinstance(body_val, (dict, list)):
                lines.append(f"    data_body = {repr(body_val)}")
            elif body_val is None:
                lines.append("    data_body = None")
            else:
                # 字符串也允许（不推荐）
                lines.append(f"    data_body = {repr(body_val)}")
            lines.append("    json_body = None")
        else:
            # raw / multipart/form-data（V1 先当 raw/json 处理字段）
            if isinstance(body_val, (dict, list)):
                lines.append(f"    json_body = {repr(body_val)}")
            elif body_val is None:
                lines.append("    json_body = None")
            else:
                lines.append(f"    json_body = {repr(body_val)}")
            lines.append("    data_body = None")

        lines.append("    resp = send_request(url, method, headers=headers, params=params, json_body=json_body, data_body=data_body, timeout=10)")
        lines.append("")

        # assertions
        assertions: list[dict] = step.get("assertions", [])
        if assertions:
            lines.append("    # assertions")
            for a in assertions:
                target_py = a["target_py"]
                assert_line = a["assert_line"]
                # 断言语句已经是纯 Python
                lines.append(f"    {assert_line}")
            lines.append("")
        else:
            lines.append("    # no assertions")
            lines.append("")

    return "\n".join(lines) + "\n"


# ===================== 主入口：创建脚本 =====================
def create_test_script(project_name: str, testcase_title: str) -> str:
    """
    在某个项目下，按 testcase_title 找用例，生成 pytest 文件到：
      {testbench_root}/casefile/{项目名}/test_{项目名}_{0001}_{用例名}.py

    返回生成文件的绝对路径字符串
    """
    project = Project.objects.filter(name=project_name).first()
    if not project:
        raise ValidationError(f"Project '{project_name}' not found")

    testcase = Testcase.objects.filter(project=project, title=testcase_title).first()
    if not testcase:
        raise ValidationError(f"Testcase with title '{testcase_title}' not found in project '{project_name}'")

    # 收集步骤（按 order）
    testcase_keywords = TestCaseKeyword.objects.filter(test_case=testcase).order_by("order")

    steps: list[dict] = []
    for tk in testcase_keywords:
        # 拿断言（挂在 testcase_keyword 上）
        assertions_qs = Assertion.objects.filter(testcase_keyword=tk).values("target_value", "operator", "compared_value")

        compiled_assertions = []
        for a in assertions_qs:
            target_value = a["target_value"]
            operator = a["operator"]
            compared_value = a["compared_value"]

            target_py = compile_target_value(target_value)  # -> "resp.status_code" / "resp.json()['k']"
            assert_line = compile_assertion_line(target_py, operator, compared_value)

            compiled_assertions.append({
                "target_py": target_py,
                "assert_line": assert_line,
            })

        body_value = _parse_body_text(tk.body)

        steps.append({
            "url": tk.url,
            "method": tk.method,
            "params": tk.params or {},
            "headers": tk.headers or {},
            "body_type": tk.body_type,
            "body_value": body_value,
            "assertions": compiled_assertions,
        })

    # 路径规则：testbench 根目录 / casefile / 项目名
    project_root = Path(__file__).resolve().parent.parent
    casefile_dir = project_root / "casefile"
    project_dir = casefile_dir / _safe_fs_name(project_name)
    project_dir.mkdir(parents=True, exist_ok=True)

    # seq: 0001 递增
    seq = _next_seq_num(project_dir)

    # 文件名：test_项目名_0001_用例名（testcase.name）
    file_name = f"test_{_safe_fs_name(project_name)}_{seq}_{_safe_fs_name(testcase.name)}.py"
    file_path = project_dir / file_name

    content = build_test_file_content(project_name, seq, testcase.name, steps)

    file_path.write_text(content, encoding="utf-8")
    return str(file_path)


# ===================== 可独立运行 =====================
def main():
    import argparse

    parser = argparse.ArgumentParser(description="Generate pytest script from TestBench DB testcase")
    parser.add_argument("--project", required=True, help="Project.name, e.g. 'Project A'")
    parser.add_argument("--title", required=True, help="Testcase.title, e.g. 'eiptest'")
    args = parser.parse_args()

    out = create_test_script(args.project, args.title)
    print(f"[OK] Generated: {out}")


if __name__ == "__main__":
    main()
