"""
sql_cleaner.py

提供 SQL 清理相關工具，移除註解並標準化格式，
方便比對 Stored Procedure、View、Trigger 等定義內容。
"""

import re

def remove_sql_comments(sql_text: str) -> str:
    """
    移除單行註解 (-- ...) 與多行註解 (/* ... */)

    Args:
        sql_text (str): 原始 SQL 字串

    Returns:
        str: 去除註解後的 SQL 字串
    """
    if not sql_text:
        return sql_text
    sql_text = re.sub(r'--.*', '', sql_text)
    sql_text = re.sub(r'/\*.*?\*/', '', sql_text, flags=re.DOTALL)
    return sql_text.strip()

def clean_definition_lines(sql_text: str) -> list[str]:
    """
    將 SQL 字串拆成逐行、去除註解與空白，轉為小寫，方便比對

    Args:
        sql_text (str): 原始 SQL 定義

    Returns:
        list[str]: 處理後的每一行內容（小寫、去除空白與註解）
    """
    sql_text = remove_sql_comments(sql_text)
    return [line.strip().lower() for line in sql_text.splitlines() if line.strip()]
