"""
result_writer.py

負責將比對結果輸出至 console、JSON 或 CSV 檔案。
"""

import json
import csv

def save_results(results: dict, output_format: str = "console", output_file: str = None):
    """
    儲存比對結果

    Args:
        results (dict): 分層格式為 {server: {database: {object: [differences]}}}
        output_format (str): 'json', 'csv', 或 'console'
        output_file (str): 輸出檔名，若為 None 則印出於 console
    """
    if output_format == "json":
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4, ensure_ascii=False)

    elif output_format == "csv":
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Server", "Database", "Object", "Differences"])
            for server, databases in results.items():
                for database, objects in databases.items():
                    for name, diffs in objects.items():
                        diff_text = "\n".join(diffs) if isinstance(diffs, list) else str(diffs)
                        writer.writerow([server, database, name, diff_text])

    else:
        for server, databases in results.items():
            print(f"\n======= {server} =======")
            for database, objects in databases.items():
                print(f"Database: {database}")
                for name, diffs in objects.items():
                    print(f"  Object: {name}")
                    lines = diffs if isinstance(diffs, list) else [diffs]
                    for diff in lines:
                        print(f"    {diff}")
