const QIANJI_FIELDS = [
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
];

function formatToday() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function cleanHeader(value) {
  return String(value || '').replace(/^\uFEFF/, '').trim();
}

function parseDate(value) {
  if (!value) {
    return null;
  }
  const parts = value.trim().split('/');
  if (parts.length !== 3) {
    return null;
  }
  const [day, month, year] = parts;
  if (!day || !month || !year) {
    return null;
  }
  return `${year}/${month.padStart(2, '0')}/${day.padStart(2, '0')} 00:00`;
}

function parseNumber(value) {
  if (value === undefined || value === null) {
    return null;
  }
  const raw = String(value).replace(/[\s,]/g, '');
  const num = Number(raw);
  return Number.isFinite(num) ? num : null;
}

function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = '';
  let inQuotes = false;

  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];

    if (char === '"') {
      if (inQuotes && text[i + 1] === '"') {
        field += '"';
        i += 1;
      } else {
        inQuotes = !inQuotes;
      }
      continue;
    }

    if (char === ',' && !inQuotes) {
      row.push(field);
      field = '';
      continue;
    }

    if ((char === '\n' || char === '\r') && !inQuotes) {
      if (char === '\r' && text[i + 1] === '\n') {
        i += 1;
      }
      row.push(field);
      field = '';
      if (row.some((cell) => String(cell).trim() !== '')) {
        rows.push(row);
      }
      row = [];
      continue;
    }

    field += char;
  }

  row.push(field);
  if (row.some((cell) => String(cell).trim() !== '')) {
    rows.push(row);
  }

  return rows;
}

function rowsToObjects(rows) {
  if (!rows.length) {
    return [];
  }
  const headers = rows[0].map(cleanHeader);
  const data = [];

  for (let i = 1; i < rows.length; i += 1) {
    const row = rows[i];
    if (!row || row.every((cell) => String(cell).trim() === '')) {
      continue;
    }
    const item = {};
    headers.forEach((header, index) => {
      item[header] = row[index] !== undefined ? String(row[index]).trim() : '';
    });
    data.push(item);
  }

  return data;
}

function escapeCsv(value) {
  const text = value === undefined || value === null ? '' : String(value);
  if (/[",\n]/.test(text)) {
    return `"${text.replace(/"/g, '""')}"`;
  }
  return text;
}

function buildCsv(rows) {
  return rows.map((row) => row.map(escapeCsv).join(',')).join('\n');
}

function convertHsbc(rows) {
  const output = [QIANJI_FIELDS];
  rows.forEach((row) => {
    const date = parseDate(row['Transaction date']);
    const amount = parseNumber(row['Billing amount']);
    if (!date || amount === null) {
      return;
    }
    const description = String(row['Description'] || '')
      .replace(/CHN\s+CN/g, '')
      .trim();
    const merchant = String(row['Merchant name'] || '').trim();
    const type = amount < 0 ? '支出' : '收入';

    output.push([
      date,
      description,
      type,
      Math.abs(amount),
      merchant,
      '',
      'pulse信用卡',
      '',
      '',
      '',
      '',
      '',
    ]);
  });
  return output;
}

function convertBea(rows) {
  const output = [QIANJI_FIELDS];
  rows.forEach((row) => {
    const date = parseDate(row['交易日期']);
    const amount = parseNumber(row['金額']);
    if (!date || amount === null) {
      return;
    }
    const description = String(row['賬項說明'] || row['账项说明'] || '').trim();
    const type = amount > 0 ? '支出' : '收入';

    output.push([
      date,
      description,
      type,
      Math.abs(amount),
      description,
      '',
      'BEA信用卡',
      '',
      '',
      '',
      '',
      '',
    ]);
  });
  return output;
}

function downloadCsv(content, filename) {
  const blob = new Blob([`\uFEFF${content}`], {
    type: 'text/csv;charset=utf-8',
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function setupConverter(prefix, converter) {
  const fileInput = document.getElementById(`${prefix}File`);
  const button = document.getElementById(`${prefix}Convert`);
  const status = document.getElementById(`${prefix}Status`);

  button.addEventListener('click', async () => {
    const file = fileInput.files[0];
    if (!file) {
      status.textContent = '请先选择账单文件。';
      return;
    }
    status.textContent = '处理中...';
    try {
      const text = await file.text();
      const rows = rowsToObjects(parseCsv(text));
      const outputRows = converter(rows);
      if (outputRows.length <= 1) {
        status.textContent = '未找到可转换的记录，请检查文件格式。';
        return;
      }
      const csvContent = buildCsv(outputRows);
      const filename = `${prefix}_qianji_output_${formatToday()}.csv`;
      downloadCsv(csvContent, filename);
      status.textContent = `完成：${outputRows.length - 1} 条记录已导出。`;
    } catch (error) {
      status.textContent = `处理失败：${error.message || error}`;
    }
  });
}

setupConverter('hsbc', convertHsbc);
setupConverter('bea', convertBea);
