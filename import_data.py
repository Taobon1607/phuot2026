import pandas as pd
import requests
import json
import time

DB_URL = "https://phuot2026-default-rtdb.asia-southeast1.firebasedatabase.app"

def import_data():
    file_path = "Chi Phi 30.4.2026.xlsx"
    
    # --- Load Expenses (Sheet '30.4') ---
    df_exp = pd.read_excel(file_path, sheet_name='30.4')
    df_exp = df_exp.where(pd.notnull(df_exp), None)
    
    expenses = []
    # Items start from row 3 (0-indexed) to row 10
    # "Vé máy bay" to "Túi nước tắm"
    for i in range(3, 11):
        row = df_exp.iloc[i]
        desc = row['Unnamed: 0']
        total_amt = row['Unnamed: 1']
        
        if desc == "Túi nước tắm":
            # Special case: split between Tam Tú (gd1) and Chi Hào (gd2)
            amt = int(total_amt) // 2
            expenses.append({
                "desc": f"{desc} (Phần gd1)",
                "amt": amt,
                "who": "gd1",
                "fam": "gd1",
                "day": "25/04",
                "cat": "🍜",
                "time": "12:00"
            })
            expenses.append({
                "desc": f"{desc} (Phần gd2)",
                "amt": amt,
                "who": "gd2",
                "fam": "gd2",
                "day": "25/04",
                "cat": "🍜",
                "time": "12:00"
            })
        elif total_amt:
            expenses.append({
                "desc": desc,
                "amt": int(total_amt),
                "who": "gd1",
                "fam": "all",
                "day": "25/04",
                "cat": "🏨" if "Hotel" in desc or "Khách sạn" in desc or "Homestay" in desc else "🍜",
                "time": "12:00"
            })

    # --- Load Hotels (Sheet 'Khách sạn') ---
    df_hotel = pd.read_excel(file_path, sheet_name='Khách sạn')
    df_hotel = df_hotel.where(pd.notnull(df_hotel), None)
    
    hotels = []
    for i in range(1, 6): # Skip header
        row = df_hotel.iloc[i]
        day_str = str(row['Unnamed: 0'])
        name = row['Unnamed: 1']
        price = row['Unnamed: 3']
        deposit = row['Unnamed: 4']
        phone = row['Unnamed: 6']
        addr = row['Unnamed: 7']
        note = row['Unnamed: 8']
        
        # Determine label from name or address
        label = "Nha Trang"
        if "Cam Ranh" in str(addr) or "Cam Ranh" in str(name): label = "Cam Ranh"
        elif "Quy Nhơn" in str(addr) or "Quy Nhơn" in str(name): label = "Quy Nhơn"
        elif "Huế" in str(addr) or "Huế" in str(name): label = "Huế"
        elif "Hà Tĩnh" in str(addr) or "Hà Tĩnh" in str(name): label = "Hà Tĩnh"

        hotels.append({
            "num": f"{i:02d}",
            "label": label,
            "dates": day_str,
            "name": name,
            "confirm": "Đã đặt",
            "price": int(price) if price else 0,
            "deposit": int(deposit) if deposit else 0,
            "phone": str(phone) if phone else "",
            "maps": "" # Not in excel
        })

    # --- Firebase Operations ---
    print("Clearing old expenses...")
    res = requests.delete(f"{DB_URL}/expenses.json")
    print(f"Delete expenses: {res.status_code}")
    
    print("Clearing old hotels...")
    res = requests.delete(f"{DB_URL}/hotel.json")
    print(f"Delete hotels: {res.status_code}")
    
    print("Uploading new expenses...")
    for exp in expenses:
        res = requests.post(f"{DB_URL}/expenses.json", json=exp)
        print(f"Added expense {exp['desc']}: {res.status_code}")
        
    print("Uploading new hotels...")
    # Use PUT with incremental keys to maintain order if needed, or just push
    hotel_data = {str(int(time.time()*1000) + i): h for i, h in enumerate(hotels)}
    res = requests.patch(f"{DB_URL}/hotel.json", json=hotel_data)
    print(f"Updated hotels: {res.status_code}")

if __name__ == "__main__":
    import_data()
