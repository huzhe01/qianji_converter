import csv
import json
from pathlib import Path
import tempfile
import unittest

from qianji_converter import _parse_date, convert_bea_to_qianji, convert_hsbc_to_qianji


class DateTests(unittest.TestCase):
    def test_date_formats(self):
        cases = json.loads(Path(__file__).with_name('date-cases.json').read_text())
        for value, expected in cases['valid']:
            with self.subTest(value=value):
                self.assertEqual(_parse_date(value), expected)
        for value in cases['invalid']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                _parse_date(value)

    def test_csv_conversion(self):
        cases = [
            (convert_bea_to_qianji,
             '交易日期,賬項說明,金額\n2026/09/28,Example shop,76.17\n05/09/2026,Example refund,-16.8\n',
             ['2026/09/28 00:00', '2026/09/05 00:00']),
            (convert_hsbc_to_qianji,
             'Transaction date,Billing amount,Description,Merchant name\n05/09/2026,-26.8,Example,Example\n',
             ['2026/09/05 00:00']),
        ]
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'input.csv'
            target = Path(directory) / 'output.csv'
            for convert, content, expected in cases:
                with self.subTest(converter=convert.__name__):
                    source.write_text(content, encoding='utf-8-sig')
                    convert(source, target)
                    with target.open(encoding='utf-8', newline='') as output:
                        rows = list(csv.DictReader(output))
                    self.assertEqual([row['时间'] for row in rows], expected)
                    self.assertEqual(rows[0]['类型'], '支出')


if __name__ == '__main__':
    unittest.main()
