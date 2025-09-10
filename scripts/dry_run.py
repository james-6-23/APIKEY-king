import os
import sys
import re
from typing import List

# 确保项目根目录在路径中
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from common.config import Config  # noqa: E402
from utils.file_manager import file_manager  # noqa: E402


def main() -> None:
    # 准备一段包含 base_url 与示例 ms-key 的文本内容
    base_url = "https://api-inference.modelscope.cn/v1/"
    sample_keys = [
        "ms-30184ba8-077f-4abf-a40d-97e8d6fc7cb7",
        "ms-74b8eedd-5f76-419a-a513-f421399093da",
        "ms-680eeefa-cba1-44f5-ab9e-9098e7e6fc4c",
    ]
    content = f"""
    // demo code
    const BASE = "{base_url}";
    // Some config and comments
    const MS_KEY_1 = "{sample_keys[0]}"; // token
    // ... other lines ...
    /* multiline block */
    var secret = '{sample_keys[1]}';
    // close to base url
    fetch('{base_url}infer', {{ headers: {{ Authorization: 'Bearer {sample_keys[2]}' }} }});
    """

    # 简化版：直接使用与 app 中一致的提取逻辑
    # 为避免导入 app/hajimi_king.py 触发多余线程，这里内嵌同样的抽取实现
    strict_pat = r'(?i)\bms-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b'
    loose_pat = r'(?i)\bms-[0-9a-f-]{30,}\b'

    # 判断是否包含任一 base_url
    base_urls = Config.TARGET_BASE_URLS or [base_url]
    lc = content.lower()
    positions: List[int] = []
    for u in base_urls:
        s = 0
        u = (u or "").lower()
        while u:
            i = lc.find(u, s)
            if i == -1:
                break
            positions.append(i)
            s = i + 1

    if not positions:
        print("[dry-run] 未发现 base_url，提取被跳过")
        return

    use_loose = Config.parse_bool(Config.MS_USE_LOOSE_PATTERN)
    pattern = re.compile(loose_pat if use_loose else strict_pat)
    proximity = Config.MS_PROXIMITY_CHARS if use_loose else 0
    require_ctx = Config.parse_bool(Config.MS_REQUIRE_KEY_CONTEXT)
    ctx_re = re.compile(r"(key|token|secret|authorization|api[-_ ]?key)", re.I)

    found: List[str] = []
    for m in pattern.finditer(content):
        k = m.group(0)
        if k.lower() == "ms-00000000-0000-0000-0000-000000000000":
            continue
        if proximity:
            pos = m.start()
            if not any(abs(pos - bp) <= proximity for bp in positions):
                continue
        if require_ctx:
            s = max(0, m.start() - 80)
            e = min(len(content), m.end() + 80)
            if not ctx_re.search(content[s:e]):
                continue
        found.append(k)

    # 去重且保序
    seen = set()
    found = [x for x in found if not (x in seen or seen.add(x))]

    if not found:
        print("[dry-run] 未提取到任何 ms-key（可考虑开启宽松模式或放宽距离）")
        return

    # 使用 FileManager 的落盘逻辑
    repo_name = "dry-run/demo-repo"
    file_path = "src/demo.ts"
    file_url = "https://example.com/dry-run/src/demo.ts"

    file_manager.save_valid_keys(repo_name, file_path, file_url, found)

    print("[dry-run] 提取成功并已写入：")
    print(f"  keys: {found}")
    print(f"  keys 文件: {file_manager.keys_valid_filename}")
    print(f"  详细日志: {file_manager.detail_log_filename}")


if __name__ == "__main__":
    main()

