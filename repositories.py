from models import Room, Service

class RoomRepository:
    def __init__(self, cursor):
        self.cursor = cursor

    def get_all(self):
        query = """
            SELECT p.SoPhong, p.TrangThai, p.MaLP, lp.TenLP, lp.GiaTheoNgay, lp.SucChua, p.GhiChu
            FROM Phong p JOIN LoaiPhong lp ON p.MaLP = lp.MaLP
        """
        self.cursor.execute(query)
        results = []
        for r in self.cursor.fetchall():
            note_val = r[6] if r[6] is not None else ""
            
            room_obj = Room(r[0], r[1], r[2], r[3], float(r[4]), r[5], note_val)
            results.append(room_obj)
        return results

    def get_conflict_ids(self, s_date, e_date):
        query = """
            SELECT SoPhong FROM PhieuDatPhong 
            WHERE TrangThaiDat IN (N'Đã cọc', N'Đã xác nhận', N'Đang ở')
            AND (NgayDen < ? AND NgayDi > ?)
        """
        self.cursor.execute(query, (e_date, s_date))
        return [r[0] for r in self.cursor.fetchall()]

    def update_status(self, room_id, status):
        # Check current status first
        self.cursor.execute("SELECT TrangThai FROM Phong WHERE SoPhong = ?", (room_id,))
        row = self.cursor.fetchone()
        if not row: return False, "Phòng không tồn tại."
        if row[0] == 'Đang ở' and status == 'Trống':
            return False, "CẢNH BÁO: Phòng đang có khách. Phải Checkout trước."
        
        self.cursor.execute("UPDATE Phong SET TrangThai = ? WHERE SoPhong = ?", (status, room_id))
        self.cursor.commit()
        return True, f"Cập nhật {room_id} -> {status}"
    
    def update_note(self, room_id, note):
        try:
            self.cursor.execute("UPDATE Phong SET GhiChu = ? WHERE SoPhong = ?", (note, room_id))
            self.cursor.commit()
            return True, "Đã lưu ghi chú thành công."
        except Exception as e:
            return False, f"Lỗi lưu ghi chú: {e}"

class ServiceRepository:
    def __init__(self, cursor):
        self.cursor = cursor

    def get_all(self):
        self.cursor.execute("SELECT * FROM DichVu")
        return [Service(r[0], r[1], float(r[2])) for r in self.cursor.fetchall()]

    def add_usage(self, room_id, service_id, qty):
        try:
            self.cursor.execute("SELECT MaPD FROM PhieuDatPhong WHERE SoPhong = ? AND TrangThaiDat = N'Đang ở'", (room_id,))
            row = self.cursor.fetchone()
            if not row: return False, "Phòng chưa có khách check-in."
            ma_pd = row[0]
            
            self.cursor.execute("SELECT MaSD, SoLuong FROM ChiTietSD WHERE MaPD = ? AND MaDV = ?", (ma_pd, service_id))
            existing_item = self.cursor.fetchone()
            
            if existing_item:
                new_qty = existing_item[1] + qty
                self.cursor.execute("UPDATE ChiTietSD SET SoLuong = ? WHERE MaSD = ?", (new_qty, existing_item[0]))
                action = "Cập nhật"
            else:
                self.cursor.execute("INSERT INTO ChiTietSD (MaPD, MaDV, SoLuong) VALUES (?, ?, ?)", (ma_pd, service_id, qty))
                action = "Thêm mới"
                
            self.cursor.commit()
            return True, f"{action} dịch vụ thành công."
        except Exception as e:
            return False, str(e)

class OperationRepository:
    """Xử lý các giao dịch phức tạp: Đặt phòng, Checkin, Checkout"""
    def __init__(self, conn):
        self.conn = conn
        self.cursor = conn.cursor()

    def create_booking(self, guest_info, room_ids, s_date, e_date):
        try:
            name, cccd, phone = guest_info
            
            # --- LOGIC MỚI: KIỂM TRA KHÁCH HÀNG TỒN TẠI ---
            self.cursor.execute("SELECT MaKH FROM KhachHang WHERE CCCD = ?", (cccd,))
            row = self.cursor.fetchone()
            
            if row:
                # Nếu đã có -> Update thông tin mới nhất
                makh = row[0]
                self.cursor.execute("""
                    UPDATE KhachHang SET TenKH = ?, SDT = ? WHERE MaKH = ?
                """, (name, phone, makh))
            else:
                # Nếu chưa có -> Insert mới
                self.cursor.execute("""
                    INSERT INTO KhachHang(TenKH, CCCD, SDT) VALUES(?, ?, ?)
                """, (name, cccd, phone))
                self.cursor.execute("SELECT @@IDENTITY")
                makh = self.cursor.fetchone()[0]

            # --- TẠO PHIẾU ĐẶT PHÒNG ---
            for rid in room_ids:
                self.cursor.execute("""
                    INSERT INTO PhieuDatPhong(MaKH, SoPhong, NgayDen, NgayDi, TrangThaiDat)
                    VALUES(?, ?, ?, ?, N'Đã xác nhận')
                """, (makh, rid, s_date, e_date))
            
            self.conn.commit()
            return True, f"Đặt thành công cho khách {name} (Mã KH: {makh:.0f})"
        except Exception as e:
            self.conn.rollback()
            return False, str(e)

    def check_in(self, cccd):
        """Check-in tự động theo CCCD (Chỉ check-in booking hôm nay)"""
        try:
            from datetime import datetime
            today = datetime.now().date()

            query = """
                SELECT pd.MaPD, pd.SoPhong, pd.NgayDen, kh.TenKH
                FROM PhieuDatPhong pd
                JOIN KhachHang kh ON pd.MaKH = kh.MaKH
                WHERE kh.CCCD = ? 
                AND pd.TrangThaiDat = N'Đã xác nhận'
            """
            self.cursor.execute(query, (cccd,))
            bookings = self.cursor.fetchall()
            
            if not bookings:
                return False, f"Không tìm thấy phiếu đặt phòng nào cho CCCD: {cccd}"

            valid_bookings = []
            today_rooms = []
            
            for b in bookings:
                # b[2] là NgayDen
                if b[2] == today:
                    valid_bookings.append(b)
                    today_rooms.append(b[1]) 
                else:
                    pass 
            
            if not valid_bookings:
                return False, f"Khách có lịch đặt nhưng KHÔNG PHẢI HÔM NAY.\n   -> Ngày hẹn check-in: {bookings[0][2]}"

            customer_name = valid_bookings[0][3] 
            
            for vb in valid_bookings:
                ma_pd = vb[0]
                so_phong = vb[1]
                
                self.cursor.execute("UPDATE PhieuDatPhong SET TrangThaiDat = N'Đang ở' WHERE MaPD = ?", (ma_pd,))
                self.cursor.execute("UPDATE Phong SET TrangThai = N'Đang ở' WHERE SoPhong = ?", (so_phong,))
                
                self.cursor.execute("SELECT 1 FROM HoaDon WHERE MaPD = ?", (ma_pd,))
                if not self.cursor.fetchone():
                    self.cursor.execute("INSERT INTO HoaDon (MaPD, TrangThaiHD) VALUES (?, N'Chưa thanh toán')", (ma_pd,))

            self.conn.commit()
            
            return True, {
                "name": customer_name,
                "rooms": today_rooms,
                "count": len(today_rooms)
            }

        except Exception as e:
            self.conn.rollback()
            return False, f"Lỗi hệ thống: {str(e)}"

    def get_bill_raw_data(self, room_id):
        query_room = """
            SELECT hd.MaHD, hd.NgayTao, lp.GiaTheoNgay, lp.TenLP, kh.TenKH, pd.MaPD
            FROM HoaDon hd
            JOIN PhieuDatPhong pd ON hd.MaPD = pd.MaPD
            JOIN Phong p ON pd.SoPhong = p.SoPhong
            JOIN LoaiPhong lp ON p.MaLP = lp.MaLP
            JOIN KhachHang kh ON pd.MaKH = kh.MaKH
            WHERE p.SoPhong = ? AND p.TrangThai = N'Đang ở' AND hd.TrangThaiHD = N'Chưa thanh toán'
        """
        self.cursor.execute(query_room, (room_id,))
        room_data = self.cursor.fetchone()
        if not room_data: return None, "Không có thông tin hóa đơn."

        ma_pd = room_data[5]
        query_svc = "SELECT dv.TenDV, ctsd.SoLuong, dv.Gia FROM ChiTietSD ctsd JOIN DichVu dv ON ctsd.MaDV = dv.MaDV WHERE ctsd.MaPD = ?"
        self.cursor.execute(query_svc, (ma_pd,))
        
        services = [{"name": r[0], "qty": r[1], "price": float(r[2])} for r in self.cursor.fetchall()]
        
        return {
            "ma_hd": room_data[0], "check_in": room_data[1], "price": float(room_data[2]),
            "type": room_data[3], "customer": room_data[4], "ma_pd": ma_pd, "services": services
        }, "OK"

    def checkout(self, room_id, bill_detail, surcharge=0):
        try:
            final_total = bill_detail.grand_total + surcharge
            
            self.cursor.execute("""
                UPDATE HoaDon 
                SET TongTien = ?, PhuThu = ?, TrangThaiHD = N'Đã thanh toán' 
                WHERE MaHD = ?
            """, (final_total, surcharge, bill_detail.ma_hd))
            
            self.cursor.execute("""
                UPDATE Phong 
                SET TrangThai = N'Đang dọn', GhiChu = '' 
                WHERE SoPhong = ?
            """, (room_id,))
            
            self.cursor.execute("UPDATE PhieuDatPhong SET TrangThaiDat = N'Hoàn tất' WHERE MaPD = ?", (bill_detail.ma_pd,))
            
            self.conn.commit()
            return True, "Thanh toán thành công. Phòng chuyển sang 'Đang dọn'."
        except Exception as e:
            self.conn.rollback()
            return False, f"Lỗi checkout: {str(e)}"