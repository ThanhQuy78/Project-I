import time
from datetime import datetime
from database import HotelDatabase
from utils import HotelAlgorithms

def main():
    db = HotelDatabase()
    
    db.cursor.execute("SELECT COUNT(*) FROM Phong")
    if db.cursor.fetchone()[0] == 0:
        db.seed_data(n_rooms=2000)
    db.cursor.execute("SELECT COUNT(*) FROM DichVu")
    if db.cursor.fetchone()[0] == 0:
        db.seed_services()
    while True:
        print("\n" + "="*50)
        print("   HỆ THỐNG QUẢN LÝ KHÁCH SẠN (PYTHON + SQL)")
        print("="*50)
        print("1. Đặt phòng (Tư vấn, xem tình trạng, đặt nhiều phòng)")
        print("2. Tra cứu thông tin phòng (Binary Search)")
        print("3. Benchmark (Đo hiệu năng thuật toán)")
        print("4. Check-in (Nhận phòng & Tạo hóa đơn)")
        print("5. Gọi dịch vụ phòng (Room Service)")
        print("6. Xem hóa đơn tạm tính (Provisional Bill)")
        print("7. Check-out & Thanh toán")
        print("8. Quản lý trạng thái phòng (Dọn xong / Bảo trì)")
        print("0. Thoát")
        
        choice = input(">> Chọn chức năng: ")

        if choice == '1':
            try:
                print("\n--- [ĐẶT PHÒNG & CHECK-IN] ---")
                print("\n(Mặc định) Thời gian check-in 12h trưa hàng ngày")
                s_date = input("Ngày đến (YYYY-MM-DD): ")
                e_date = input("Ngày đi  (YYYY-MM-DD): ")
                datetime.strptime(s_date, "%Y-%m-%d"); datetime.strptime(e_date, "%Y-%m-%d")

                raw_rooms = db.fetch_all_rooms_raw()
                busy_ids = db.fetch_conflict_room_ids(s_date, e_date)

                print("-> Đang phân tích tình trạng phòng bằng Hash Map...")
                stats = HotelAlgorithms.analyze_availability(raw_rooms, busy_ids)

                if not stats:
                    print("Rất tiếc! Không còn phòng nào trống trong giai đoạn này.")
                    continue

                print(f"\n{'ID':<5} {'Loại Phòng':<15} {'Giá/Giờ':<12} {'Sức chứa':<10} {'CÒN TRỐNG':<10}")
                print("-" * 60)
                stats.sort(key=lambda x: x['price'])
                for s in stats:
                    print(f"{s['id']:<5} {s['name']:<15} {s['price']:<12,.0f} {s['cap']:<10} {s['count']:<10}")

                tid = int(input("\n>> Nhập ID Loại phòng muốn đặt: "))
                target_type = next((x for x in stats if x['id'] == tid), None)
                
                if not target_type:
                    print("ID không hợp lệ.")
                    continue
                
                qty = int(input(f">> Nhập số lượng phòng (Tối đa {target_type['count']}): "))
                if qty <= 0 or qty > target_type['count']:
                    print("Số lượng không hợp lệ.")
                    continue

                print("\nNhập thông tin khách hàng:")
                guest = (input("Họ tên: "), input("CCCD: "), input("SĐT: "))
                
                confirm = input(f"Xác nhận đặt {qty} phòng '{target_type['name']}'? (y/n): ")
                if confirm.lower() == 'y':
                    rooms_to_book = target_type['room_ids'][:qty]
                    ok, msg = db.execute_booking_transaction(guest, rooms_to_book, s_date, e_date)
                    print(f"KẾT QUẢ: {msg}")

            except ValueError:
                print("Lỗi nhập liệu.")

        elif choice == '2':
            try:
                rid = int(input("Nhập số phòng cần tìm: "))
                data = db.fetch_all_rooms_raw()
                sorted_data = sorted(data, key=lambda x: x['id'])
                
                st = time.time()
                res = HotelAlgorithms.binary_search_room(sorted_data, rid)
                et = time.time()
                
                if res:
                    print(f"-> Tìm thấy: Phòng {res['id']} | {res['type_name']} | Giá: {res['price']:,.0f}")
                    print(f"-> Thời gian tìm: {(et-st)*1000:.4f} ms")
                else:
                    print("Không tìm thấy phòng.")
            except: pass


        elif choice == '3':
            print("\n--- BENCHMARK REPORT ---")
            data = db.fetch_all_rooms_raw()
            print(f"Dataset: {len(data)} records")
            
            t0 = time.time()
            HotelAlgorithms.merge_sort_by_price(data)
            print(f"Merge Sort: {time.time()-t0:.5f} s")
            
            t0 = time.time()
            conflict = db.fetch_conflict_room_ids('2025-01-01', '2025-01-02') 
            HotelAlgorithms.analyze_availability(data, conflict)
            print(f"Hash Map Filter: {time.time()-t0:.5f} s")

        elif choice == '4':
            print("\n--- [CHECK-IN NHẬN PHÒNG] ---")
            try:
                rid = int(input("Nhập Mã Số Phòng khách nhận: "))
                cccd = input("Nhập CCCD của khách hàng: ")
                
                print(f"Đang kiểm tra thông tin đặt phòng...")
                
                success, msg = db.perform_check_in(rid, cccd)
                
                if success:
                    print("\n" + "*"*40)
                    print(f" {msg}")
                    print("*"*40)
                    print("-> Hệ thống đã chuyển trạng thái sang 'Đang ở'.")
                    print("-> Đã mở hóa đơn chờ thanh toán.")
                else:
                    print(f"\n LỖI CHECK-IN: {msg}")
                    print("Gợi ý: Kiểm tra lại xem khách đã đặt phòng này chưa.")
                    
            except ValueError:
                print("Lỗi nhập liệu số phòng.")
        
        elif choice == '5':
            print("\n--- [GỌI DỊCH VỤ / MINIBAR] ---")
            try:
                rid = int(input("Nhập Số Phòng cần gọi dịch vụ: "))
                
                print(f"\n{'ID':<5} {'Tên Dịch Vụ':<20} {'Đơn Giá':<15}")
                print("-" * 45)
                services = db.get_service_list()
                for s in services:
                    print(f"{s['id']:<5} {s['name']:<20} {s['price']:<15,.0f}")
                
                sid = int(input("\n>> Nhập ID Dịch vụ: "))
                
                selected_sv = next((x for x in services if x['id'] == sid), None)
                if not selected_sv:
                    print("Lỗi: Mã dịch vụ không tồn tại.")
                    continue
                    
                qty = int(input(f">> Nhập số lượng '{selected_sv['name']}': "))
                if qty <= 0: 
                    print("Số lượng phải lớn hơn 0.")
                    continue

                ok, msg = db.add_service_usage(rid, sid, qty)
                
                if ok:
                    total = qty * selected_sv['price']
                    print("\n" + "*"*40)
                    print(f" GỌI MÓN THÀNH CÔNG!")
                    print(f"   + Món: {selected_sv['name']}")
                    print(f"   + SL:  {qty}")
                    print(f"   + Tổng tiền: {total:,.0f} VND")
                    print("   -> Đã ghi vào hóa đơn phòng.")
                    print("*"*40)
                else:
                    print(f" LỖI: {msg}")

            except ValueError:
                print("Lỗi nhập liệu.")
        elif choice in ['6', '7']:
            try:
                rid = int(input("Nhập Số Phòng: "))
                
                raw_data, msg = db.get_bill_info(rid)
                
                if not raw_data:
                    print(f" {msg}")
                    continue

                bill = HotelAlgorithms.calculate_bill_details(raw_data)

                print("\n" + "="*50)
                title = "HÓA ĐƠN TẠM TÍNH" if choice == '8' else "HÓA ĐƠN THANH TOÁN"
                print(f"{title:^50}")
                print("="*50)
                print(f"Khách hàng: {bill['customer']}")
                print(f"Check-in:   {bill['check_in'].strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"Check-out:  {bill['check_out'].strftime('%Y-%m-%d %H:%M:%S')}")
                print("-" * 50)
                
                print(f"1. TIỀN PHÒNG ({bill['hours']} giờ x {bill['room_price']:,.0f})")
                print(f"{' ':>40} {bill['room_total']:,.0f} VND")
                
                print(f"2. DỊCH VỤ")
                if not bill['services']:
                    print("   (Không sử dụng dịch vụ)")
                else:
                    for s in bill['services']:
                        print(f"   - {s['name']:<20} x{s['qty']:<3} {s['subtotal']:,.0f}")
                print(f"{' ':>40} {bill['service_total']:,.0f} VND")
                
                print("-" * 50)
                print(f"TỔNG CỘNG:{' ':>29} {bill['grand_total']:,.0f} VND")
                print("="*50)

                if choice == '7':
                    confirm = input("\nXác nhận thanh toán và trả phòng? (y/n): ")
                    if confirm.lower() == 'y':
                        ok, res_msg = db.process_checkout(rid, bill['grand_total'])
                        if ok:
                            print(f"\n {res_msg}")
                            print(f"[System] Trạng thái phòng {rid} đã chuyển sang 'Đang dọn'.")
                        else:
                            print(f"\n Lỗi: {res_msg}")
            
            except ValueError:
                print("Lỗi nhập liệu.")

        elif choice == '8':
            print("\n--- [QUẢN LÝ TRẠNG THÁI PHÒNG] ---")
            try:
                rid = int(input("Nhập Số Phòng cần cập nhật: "))
                
                print("Chọn trạng thái mới:")
                print("1. Trống (Sẵn sàng đón khách)")
                print("2. Đang dọn (Cleaning)")
                print("3. Bảo trì (Maintenance)")
                
                st_choice = input(">> Chọn trạng thái (1-3): ")
                
                status_map = {
                    '1': 'Trống',
                    '2': 'Đang dọn',
                    '3': 'Bảo trì'
                }
                
                if st_choice in status_map:
                    new_st = status_map[st_choice]
                    
                    confirm = input(f"Chuyển phòng {rid} sang '{new_st}'? (y/n): ")
                    if confirm.lower() == 'y':
                        msg = db.update_room_status(rid, new_st)
                        print(f"\nThành công {msg}")
                else:
                    print("Lựa chọn không hợp lệ.")
                    
            except ValueError:
                print("Lỗi nhập liệu (Vui lòng nhập số).")

        elif choice == '0':
            break

if __name__ == "__main__":
    main()