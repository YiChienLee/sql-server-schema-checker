"""
db_reader.py

提供統一的 Excel 讀取介面，用於讀取資料庫連線資訊、
資料表清單、SP 清單、View 清單等。
"""

import pandas as pd

def read_db_info(filepath: str) -> tuple[dict, list[dict]]:
    """
    從 Excel 中讀取資料庫帳號與連線資訊。

    Args:
        filepath (str): Excel 檔案路徑（如 Account.xlsx）

    Returns:
        tuple: (基準資料庫, 目標資料庫清單)
    """
    df = pd.read_excel(filepath, dtype=str)
    db_list = df.to_dict(orient="records")
    if len(db_list) < 2:
        raise ValueError("Excel 檔案內至少要有兩列資料，第一列為基準資料庫")
    return db_list[0], db_list[1:]

def read_list_from_excel(filepath: str, column_name: str = None) -> list[str]:
    """
    從 Excel 讀取比對用的清單（SP、View、Table）

    Args:
        filepath (str): Excel 檔案路徑
        column_name (str): 欄位標題，如 'SP Name'，若無則取第一欄

    Returns:
        list[str]: 清單內容（已去除空白與標題列）
    """
    df = pd.read_excel(filepath, dtype=str)
    values = df.iloc[:, 0].dropna().tolist()
    if values and values[0].strip().lower() == (column_name or "").strip().lower():
        values = values[1:]
    if not values:
        raise ValueError(f"Excel 檔案內至少要有一個 {column_name or '名稱'}")
    return values
