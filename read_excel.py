import pandas as pd
import json
import sys

def read_excel(file_path):
    try:
        # Read all sheets
        xl = pd.ExcelFile(file_path)
        data = {}
        for sheet_name in xl.sheet_names:
            df = xl.parse(sheet_name)
            # Convert NaN to None for JSON serialization
            df = df.where(pd.notnull(df), None)
            data[sheet_name] = df.to_dict(orient='records')
        print(json.dumps(data, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python read_excel.py <file_path>")
        sys.exit(1)
    read_excel(sys.argv[1])
