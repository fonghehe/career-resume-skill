"""Consistent CLI failure output with a safe next step and local help."""

from career_resume import ROOT
from pathlib import Path
import sys


class CliError(ValueError):
    """An operation error with a stable diagnostic code, separate from exit status."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def fail(error):
    """Report an operation failure; argument syntax remains argparse's concern."""
    messages = error if isinstance(error, (list, tuple)) else [error]
    text = '\n'.join(str(message) for message in messages)
    lower = text.lower()
    missing_public = any(str(message).lower().startswith('missing required file: ')
                         and not str(message).lower().startswith('missing required file: local/')
                         for message in messages)
    if isinstance(error, PermissionError):
        code = 1001
        hint = '检查源文件读取权限与目标目录写入权限；共享或只读安装请先创建可写的私人工作副本。'
    elif isinstance(error, UnicodeError) or "codec can't decode" in lower:
        code = 1002
        hint = '确认报错文件是 UTF-8 文本；保留原件，使用可读文字副本，不要覆盖原始材料。'
    elif 'symlink' in lower:
        code = 1003
        hint = '改用不含符号链接的真实目录和文件，保留原有路径及资料。'
    elif isinstance(error, FileExistsError) or any(
            phrase in lower for phrase in ('already exists', 'output exists', 'directory exists')):
        code = 1004
        hint = '选择不存在的新目标路径；保留已有安装、演示或导出包。'
    elif missing_public or 'missing or invalid release file' in lower:
        code = 1005
        hint = '获取完整运行包或源码并解压到新目录，保留已有 local/；不要创建同名空文件绕过检查。'
    elif 'missing required file: local/' in lower:
        code = 1006
        hint = '先在对应私人工作副本运行 python3 scripts/career.py init 补缺项；已有档案会保留。'
    elif isinstance(error, CliError) and error.code == 1007:
        code = 1007
        hint = '本次 Git 读取已超时并终止；先用 --details-limit 0 缩小明细范围或单独检查该仓库，再使用新的报告路径重试。'
    else:
        code = 1000
        hint = '按上方原始错误检查输入与参数；可用对应命令的 --help 查看用法，再查阅本地排错说明。'
    if isinstance(error, CliError):
        code = error.code
    for message in messages:
        print('ERROR: ' + str(message), file=sys.stderr)
    print('CODE: ' + str(code), file=sys.stderr)
    print('NEXT: ' + hint, file=sys.stderr)
    print('HELP: ' + str(ROOT / 'docs/guide/troubleshooting.md'), file=sys.stderr)
    return 1
