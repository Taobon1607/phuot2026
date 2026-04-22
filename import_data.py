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

    # --- Load Itinerary (Sheet 'Lịch trình tham quan') ---
    df_itinerary = pd.read_excel(file_path, sheet_name='Lịch trình tham quan')
    df_itinerary = df_itinerary.where(pd.notnull(df_itinerary), None)
    
    # We will manually map the itinerary from the text provided in the sheet/image
    # Since the sheet is unstructured text, we'll create the structured objects
    itinerary = [
        {
            "day": "25/04", "title": "Ngày 1: Đến Nha Trang", "sub": "Check-in & Nghỉ ngơi", "color": "#2B5F8E",
            "content": "22:00|Check-in|Dự kiến 22h00|false\n--|Nghỉ ngơi|Chọn KS gần Bãi Dài hoặc trung tâm|false"
        },
        {
            "day": "26/04", "title": "Ngày 2: Nha Trang - Vĩnh Hy", "sub": "Cung đường biển đẹp nhất", "color": "#1F6B3A",
            "content": "07:30|Di chuyển|Đi Vĩnh Hy (100km) qua Đầm Thủy Triều|false\n09:00|Tham quan|Hang Rái & Vịnh Vĩnh Hy (cano đáy kính)|false\n12:00|Ăn trưa|Hải sản nhà bè Út Thành hoặc Vui Vẻ|false\n13:30|Hái nho|Ghé Vườn nho Thái An|false\n19:00|Ăn tối|Nem nướng Đặng Văn Quyên hoặc Bò Lạc Cảnh|false"
        },
        {
            "day": "27/04", "title": "Ngày 3: Nha Trang City", "sub": "Tham quan thành phố", "color": "#C45000",
            "content": "08:00|Tham quan|Viện Hải dương học & Tháp Bà Ponagar|false\n14:00|Vui chơi|Tắm biển hoặc VinWonders|false\n18:00|Ăn uống|Bún sứa Năm Beo hoặc Cơm Niêu Thiên Lý|false"
        },
        {
            "day": "28/04", "title": "Ngày 4: Nha Trang - Quy Nhơn", "sub": "Hành trình 215km", "color": "#2B5F8E",
            "content": "07:00|Check-out|Xuất phát đi Quy Nhơn|false\n09:00|Dừng chân|Ghềnh Đá Đĩa & Tháp Nhạn (Phú Yên)|false\n12:00|Ăn trưa|Cơm gà Tuyết Nhung (Tuy Hòa)|false\n17:00|Check-in|Quy Nhơn, tối dạo phố Ngô Văn Sở|false"
        },
        {
            "day": "29/04", "title": "Ngày 5: Kỳ Co - Eo Gió", "sub": "Thiên đường biển đảo", "color": "#1F6B3A",
            "content": "08:00|Biển đảo|Cano ra đảo Kỳ Co & check-in Eo Gió|false\n14:00|Tâm linh|Thăm Tịnh xá Ngọc Hòa|false\n18:00|Hải sản|Quán Hướng Dương hoặc Hoàng Thao (Nhơn Lý)|false"
        },
        {
            "day": "30/04", "title": "Ngày 6: Quy Nhơn - Huế", "sub": "Chặng dài nhất 400km", "color": "#C45000",
            "content": "06:00|Xuất phát|Chặng dài 7-8 tiếng, đi sớm|true\n13:00|Check-in|Đến Huế, nghỉ ngơi|false\n15:00|Cố đô|Tham quan Đại Nội & Chùa Thiên Mụ|false\n19:00|Ẩm thực|Bánh Bà Đỏ, nghe ca Huế sông Hương|false"
        },
        {
            "day": "01/05", "title": "Ngày 7: Huế - Hà Tĩnh", "sub": "Hành trình 310km", "color": "#2B5F8E",
            "content": "07:00|Ăn sáng|Bún bò Huế O Phượng/Mệ Kéo|false\n10:00|Di chuyển|Ghé Vũng Chùa viếng mộ Đại tướng|false\n14:00|Hà Tĩnh|Check-in biển Thiên Cầm|false\n16:00|Di tích|Ghé Ngã ba Đồng Lộc|false\n18:00|Đặc sản|Mực nhảy Vũng Áng, kẹo Cu Đơ|false"
        }
    ]

    print("Clearing old itinerary...")
    requests.delete(f"{DB_URL}/lich.json")
    
    print("Uploading new itinerary...")
    iti_data = {str(int(time.time()*1000) + i): d for i, d in enumerate(itinerary)}
    requests.patch(f"{DB_URL}/lich.json", json=iti_data)
    print("Itinerary updated!")

    # --- Add Notes ---
    notes = [
        {
            "title": "Kiểm tra xe cá nhân",
            "body": "Trước khi đi, hãy kiểm tra lốp, phanh và dầu nhớt vì chặng đường tổng cộng khoảng hơn 1.000km.",
            "type": "warn"
        },
        {
            "title": "Đặt phòng/Nhà hàng",
            "body": "Ngày 29/04 - 01/05 là đỉnh điểm lễ. Nên chốt đặt phòng ngay và gọi điện đặt bàn trước tại các nhà hàng nổi tiếng.",
            "type": "warn"
        },
        {
            "title": "Chú ý tốc độ",
            "body": "Chú ý các biển báo hạn chế tốc độ tại khu vực dân cư ở Phú Yên và Quảng Bình (thường xuyên có kiểm soát tốc độ).",
            "type": "info"
        }
    ]

    print("Clearing old notes...")
    requests.delete(f"{DB_URL}/note.json")
    
    print("Uploading new notes...")
    note_data = {str(int(time.time()*1000) + i): n for i, n in enumerate(notes)}
    requests.patch(f"{DB_URL}/note.json", json=note_data)
    print("Notes updated!")

if __name__ == "__main__":
    import_data()
