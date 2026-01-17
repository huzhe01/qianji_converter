import pdfplumber
import pandas as pd
import re

def parse_bea_text(pdf_path):
    transactions = []
    
    # --- 核心正则逻辑 ---
    # 解释:
    # 1. ^(\d{1,2}\s+[A-Z]{3})  -> 捕获记账日期 (开头是 1-2位数字 + 空格 + 3位大写字母，如 20 NOV)
    # 2. \s+                    -> 中间可能有多个空格
    # 3. (\d{1,2}\s+[A-Z]{3})   -> 捕获交易日期 (同上)
    # 4. \s+                    -> 空格
    # 5. (.+?)                  -> 捕获描述 (商户名)，非贪婪匹配，取中间所有内容
    # 6. \s+                    -> 空格
    # 7. ([\d,]+\.\d{2}(?:CR)?)$ -> 捕获金额 (数字+小数点+两位小数，结尾可能有CR)，$表示行尾
    
    line_pattern = re.compile(r'^(\d{1,2}\s+[A-Z]{3})\s+(\d{1,2}\s+[A-Z]{3})\s+(.+?)\s+([\d,]+\.\d{2}(?:CR)?)$')

    print(f"开始处理: {pdf_path}")
    
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            # 获取该页的全部文本
            text = page.extract_text()
            if not text:
                continue
            
            print(f"--- 正在分析第 {i+1} 页 ---")
            
            # 按行分割文本
            lines = text.split('\n')
            
            for line in lines:
                line = line.strip()
                
                # 尝试匹配正则
                match = line_pattern.match(line)
                
                if match:
                    # 提取正则捕获的4个组
                    post_date = match.group(1)
                    trans_date = match.group(2)
                    desc = match.group(3)
                    amount_str = match.group(4)
                    
                    # 处理金额逻辑
                    is_credit = False
                    if 'CR' in amount_str:
                        is_credit = True
                        amount_str = amount_str.replace('CR', '')
                    
                    amount_str = amount_str.replace(',', '')
                    
                    try:
                        amount = float(amount_str)
                        if is_credit:
                            amount = -amount # 标记为负数
                            
                        transactions.append({
                            "Post Date": post_date,
                            "Trans Date": trans_date,
                            "Description": desc,
                            "Amount": amount
                        })
                        # print(f"  [提取成功] {desc} : {amount}") # 调试用
                        
                    except ValueError:
                        continue

    return pd.DataFrame(transactions)

# --- 运行 ---
pdf_file = "东亚银行电子月结单1123.pdf"

try:
    df = parse_bea_text(pdf_file)
    
    if df.empty:
        print("\n未提取到交易。请检查：\n1. PDF是否包含交易明细页（通常在第2页）\n2. 这一期账单是否有消费。")
    else:
        print(f"\n成功提取 {len(df)} 条记录")
        print(df.head())
        df.to_csv("BEA_Output.csv", index=False)
        print("已保存为 Excel")
except Exception as e:
    print(f"错误: {e}")
