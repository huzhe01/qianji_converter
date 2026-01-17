#!/usr/bin/env python3
import argparse
from datetime import datetime
from pathlib import Path

from qianji_converter import (
    convert_bea_to_qianji,
    convert_hsbc_to_qianji,
    detect_bank_from_headers,
    read_headers,
)

DEFAULT_OUTPUT_DIR = Path('/Users/huzhe/playground/hsbc2qianji/output')


def _build_output_path(bank, output_dir):
    date_str = datetime.now().strftime('%Y-%m-%d')
    filename = f'{bank}_qianji_output_{date_str}.csv'
    return output_dir / filename


def main():
    parser = argparse.ArgumentParser(
        description='将 HSBC/BEA 账单 CSV 转换为钱迹导入格式。'
    )
    parser.add_argument('input_file', help='账单 CSV 的绝对路径')
    parser.add_argument(
        '--bank',
        choices=['hsbc', 'bea', 'auto'],
        default='auto',
        help='账单类型（默认自动识别）',
    )
    parser.add_argument(
        '--output-dir',
        default=str(DEFAULT_OUTPUT_DIR),
        help='输出目录（默认写入项目 output 目录）',
    )
    args = parser.parse_args()

    input_path = Path(args.input_file).expanduser()
    if not input_path.is_absolute():
        parser.error('请输入绝对路径，例如 /Users/xxx/file.csv')
    if not input_path.exists():
        parser.error(f'文件不存在: {input_path}')

    output_dir = Path(args.output_dir).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)

    bank = args.bank
    if bank == 'auto':
        headers = read_headers(input_path)
        bank = detect_bank_from_headers(headers)
        if bank is None:
            parser.error('无法自动识别账单类型，请使用 --bank hsbc 或 --bank bea')

    output_path = _build_output_path(bank, output_dir)

    if bank == 'hsbc':
        convert_hsbc_to_qianji(input_path, output_path)
    else:
        convert_bea_to_qianji(input_path, output_path)

    print(f'已导出: {output_path}')


if __name__ == '__main__':
    main()
