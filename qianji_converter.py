import csv
import re
from datetime import datetime

QIANJI_FIELDS = [
    '时间',
    '分类',
    '类型',
    '金额',
    '账户1',
    '账户2',
    '备注',
    '账单标记',
    '手续费',
    '优惠券',
    '标签',
    '账单图片',
]


def _normalize_fieldnames(fieldnames):
    if not fieldnames:
        return fieldnames
    return [name.strip().lstrip('\ufeff') for name in fieldnames]


def read_headers(input_file, encoding='utf-8-sig'):
    with open(input_file, 'r', encoding=encoding, newline='') as infile:
        reader = csv.reader(infile)
        try:
            headers = next(reader)
        except StopIteration:
            return []
    return _normalize_fieldnames(headers)


def detect_bank_from_headers(headers):
    header_set = {name for name in headers if name}
    if {'Transaction date', 'Billing amount'}.issubset(header_set):
        return 'hsbc'
    if {'交易日期', '金額'}.issubset(header_set):
        return 'bea'
    return None


def _parse_date(value):
    return datetime.strptime(value.strip(), '%d/%m/%Y').strftime('%Y/%m/%d %H:%M')


def _parse_amount(value):
    raw_amount = str(value).replace(' ', '').replace(',', '')
    return float(raw_amount)


def convert_hsbc_to_qianji(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8-sig', newline='') as infile, open(
        output_file, 'w', newline='', encoding='utf-8'
    ) as outfile:
        reader = csv.DictReader(infile)
        reader.fieldnames = _normalize_fieldnames(reader.fieldnames)

        writer = csv.DictWriter(outfile, fieldnames=QIANJI_FIELDS)
        writer.writeheader()

        for row in reader:
            if not row or not row.get('Transaction date') or not row.get('Billing amount'):
                continue

            try:
                when = _parse_date(row['Transaction date'])
                amount = _parse_amount(row['Billing amount'])
            except ValueError:
                continue

            description = (row.get('Description') or '').strip()
            description = re.sub(r'CHN\s+CN', '', description).strip()
            merchant = (row.get('Merchant name') or '').strip()
            tx_type = '支出' if amount < 0 else '收入'

            writer.writerow(
                {
                    '时间': when,
                    '分类': description,
                    '类型': tx_type,
                    '金额': abs(amount),
                    '账户1': merchant,
                    '账户2': '',
                    '备注': 'pulse信用卡',
                    '账单标记': '',
                    '手续费': '',
                    '优惠券': '',
                    '标签': '',
                    '账单图片': '',
                }
            )


def convert_bea_to_qianji(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8-sig', newline='') as infile, open(
        output_file, 'w', newline='', encoding='utf-8'
    ) as outfile:
        reader = csv.DictReader(infile)
        reader.fieldnames = _normalize_fieldnames(reader.fieldnames)

        writer = csv.DictWriter(outfile, fieldnames=QIANJI_FIELDS)
        writer.writeheader()

        for row in reader:
            if not row or not row.get('交易日期') or not row.get('金額'):
                continue

            try:
                when = _parse_date(row['交易日期'])
                amount = _parse_amount(row['金額'])
            except ValueError:
                continue

            description = (row.get('賬項說明') or row.get('账项说明') or '').strip()
            tx_type = '支出' if amount > 0 else '收入'

            writer.writerow(
                {
                    '时间': when,
                    '分类': description,
                    '类型': tx_type,
                    '金额': abs(amount),
                    '账户1': description,
                    '账户2': '',
                    '备注': 'BEA信用卡',
                    '账单标记': '',
                    '手续费': '',
                    '优惠券': '',
                    '标签': '',
                    '账单图片': '',
                }
            )
