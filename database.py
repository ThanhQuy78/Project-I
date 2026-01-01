import pyodbc
import random

class HotelDatabase:
    def __init__(self):
        self.server = '.\\SQLEXPRESS'  
        self.database = 'HotelManagementDB'
        self.driver = '{ODBC Driver 17 for SQL Server}'
        
        self.conn = None
        self.cursor = None
        self.connect_and_initialize()

    def connect_and_initialize(self):
        """Kết nối và tự động tạo DB/Bảng nếu chưa có"""
        try:
            conn_str_master = f'DRIVER={self.driver};SERVER={self.server};Trusted_Connection=yes;AutoCommit=True;'
            cnxn = pyodbc.connect(conn_str_master, autocommit=True)
            crsr = cnxn.cursor()
            
            crsr.execute(f"SELECT name FROM master.dbo.sysdatabases WHERE name = '{self.database}'")
            if not crsr.fetchone():
                print(f"[SYSTEM] Tạo Database '{self.database}'...")
                crsr.execute(f"CREATE DATABASE {self.database}")
            cnxn.close()

            self.conn = pyodbc.connect(f'DRIVER={self.driver};SERVER={self.server};DATABASE={self.database};Trusted_Connection=yes;')
            self.cursor = self.conn.cursor()
            
            self._create_tables()
            print("[SYSTEM] Kết nối SQL Server thành công.")
            
        except Exception as e:
            print(f"[CRITICAL ERROR] Không thể kết nối SQL Server: {e}")
            print("Gợi ý: Kiểm tra lại tên SERVER trong code hoặc cài ODBC Driver.")
            exit()

    def _create_tables(self):
        """Tạo bảng theo thiết kế trong tài liệu"""
        self.cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='KhachHang' AND xtype='U')
            CREATE TABLE KhachHang (
                MaKH INT IDENTITY(1,1) PRIMARY KEY,
                TenKH NVARCHAR(100),
                CCCD NVARCHAR(20) UNIQUE,
                SDT NVARCHAR(15)
            )
        """)
        self.cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='LoaiPhong' AND xtype='U')
            CREATE TABLE LoaiPhong (
                MaLP INT PRIMARY KEY,
                TenLP NVARCHAR(50),
                GiaTheoGio DECIMAL(18, 0),
                SucChua INT DEFAULT 2
            )
        """)
        self.cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Phong' AND xtype='U')
            CREATE TABLE Phong (
                SoPhong INT PRIMARY KEY,
                TrangThai NVARCHAR(50), 
                MaLP INT,
                FOREIGN KEY(MaLP) REFERENCES LoaiPhong(MaLP)
            )
        """)
        self.cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='PhieuDatPhong' AND xtype='U')
            CREATE TABLE PhieuDatPhong (
                MaPD INT IDENTITY(1,1) PRIMARY KEY,
                MaKH INT,
                SoPhong INT,
                NgayDen DATE,
                NgayDi DATE,
                TrangThaiDat NVARCHAR(50),
                FOREIGN KEY(MaKH) REFERENCES KhachHang(MaKH),
                FOREIGN KEY(SoPhong) REFERENCES Phong(SoPhong)
            )
        """)

        self.cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='HoaDon' AND xtype='U')
            CREATE TABLE HoaDon (
                MaHD INT IDENTITY(1,1) PRIMARY KEY,
                NgayTao DATETIME DEFAULT GETDATE(),
                MaPD INT,
                TongTien DECIMAL(18, 0) DEFAULT 0,
                TrangThaiHD NVARCHAR(50) DEFAULT N'Chưa thanh toán', -- Mới tạo
                FOREIGN KEY(MaPD) REFERENCES PhieuDatPhong(MaPD)
            )
        """)

        self.cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='DichVu' AND xtype='U')
            CREATE TABLE DichVu (
                MaDV INT PRIMARY KEY,
                TenDV NVARCHAR(50),
                Gia DECIMAL(18, 0)
            )
        """)

        self.cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='ChiTietSD' AND xtype='U')
            CREATE TABLE ChiTietSD (
                MaSD INT IDENTITY(1,1) PRIMARY KEY,
                MaPD INT,
                MaDV INT,
                SoLuong INT,
                ThoiGian DATETIME DEFAULT GETDATE(),
                FOREIGN KEY(MaPD) REFERENCES PhieuDatPhong(MaPD),
                FOREIGN KEY(MaDV) REFERENCES DichVu(MaDV)
            )
        """)
        self.conn.commit()

    def seed_data(self, n_rooms=2000):
        """Sinh dữ liệu giả lập (Mock Data)"""
        print(f"[SYSTEM] Đang sinh dữ liệu mẫu ({n_rooms} phòng)... Vui lòng đợi.")
        
        loai_phongs = [
            (1, 'Standard', 150000, 2), (2, 'Superior', 250000, 2),
            (3, 'Deluxe', 400000, 2), (4, 'Family', 600000, 4),
            (5, 'President', 1500000, 4)
        ]
        for lp in loai_phongs:
            self.cursor.execute("IF NOT EXISTS (SELECT 1 FROM LoaiPhong WHERE MaLP=?) INSERT INTO LoaiPhong VALUES (?,?,?,?)", lp)

        batch_data = []
        statuses = ['Trống', 'Đang ở', 'Đang dọn', 'Bảo trì']
        for i in range(101, 101 + n_rooms):
            batch_data.append((i, random.choice(statuses), random.randint(1, 5)))
        
        query = """
            MERGE Phong AS target
            USING (VALUES (?, ?, ?)) AS source (SoPhong, TrangThai, MaLP)
            ON target.SoPhong = source.SoPhong
            WHEN MATCHED THEN UPDATE SET TrangThai = source.TrangThai
            WHEN NOT MATCHED THEN INSERT (SoPhong, TrangThai, MaLP) VALUES (source.SoPhong, source.TrangThai, source.MaLP);
        """
        batch_size = 500
        for i in range(0, len(batch_data), batch_size):
            self.cursor.executemany(query, batch_data[i:i+batch_size])
        
        self.conn.commit()
        print("[SYSTEM] Dữ liệu đã sẵn sàng.")

    def fetch_all_rooms_raw(self):
        """Lấy toàn bộ danh sách phòng và thông tin loại phòng"""
        query = """
            SELECT p.SoPhong, p.TrangThai, p.MaLP, lp.TenLP, lp.GiaTheoGio, lp.SucChua
            FROM Phong p JOIN LoaiPhong lp ON p.MaLP = lp.MaLP
        """
        self.cursor.execute(query)
        return [
            {"id": r[0], "status": r[1], "type_id": r[2], "type_name": r[3], 
             "price": float(r[4]), "cap": r[5]} 
            for r in self.cursor.fetchall()
        ]

    def fetch_conflict_room_ids(self, s_date, e_date):
        """Lấy danh sách ID các phòng bị trùng lịch (Conflict)"""
        query = """
            SELECT SoPhong FROM PhieuDatPhong 
            WHERE TrangThaiDat IN (N'Đã cọc', N'Đã xác nhận', N'Đang ở')
            AND (NgayDen < ? AND NgayDi > ?)
        """
        self.cursor.execute(query, (e_date, s_date))
        return [r[0] for r in self.cursor.fetchall()]

    def execute_booking_transaction(self, guest_info, rooms_to_book, s_date, e_date):
        """Thực hiện lưu vào DB: Khách hàng -> Phiếu đặt -> Update Phòng"""
        try:
            name, cccd, phone = guest_info
            
            self.cursor.execute("SELECT MaKH FROM KhachHang WHERE CCCD = ?", (cccd,))
            row = self.cursor.fetchone()
            if row:
                makh = row[0]
            else:
                self.cursor.execute("INSERT INTO KhachHang(TenKH, CCCD, SDT) VALUES(?,?,?)", (name, cccd, phone))
                self.cursor.execute("SELECT @@IDENTITY")
                makh = self.cursor.fetchone()[0]

            for rid in rooms_to_book:
                self.cursor.execute("""
                    INSERT INTO PhieuDatPhong(MaKH, SoPhong, NgayDen, NgayDi, TrangThaiDat)
                    VALUES(?, ?, ?, ?, N'Đã xác nhận')
                """, (makh, rid, s_date, e_date))
                
                self.cursor.execute("UPDATE Phong SET TrangThai = N'Đã đặt' WHERE SoPhong = ?", (rid,))
            
            self.conn.commit()
            return True, f"Thành công! Mã khách hàng: {makh}"
        except Exception as e:
            self.conn.rollback()
            return False, str(e)
        
    def perform_check_in(self, room_id, customer_cccd):
        """
        Thực hiện quy trình Check-in (UC1):
        1. Kiểm tra xem có phiếu đặt phòng 'Đã xác nhận' cho phòng này và khách này không.
        2. Chuyển trạng thái Phiếu & Phòng sang 'Đang ở'.
        3. Tạo Hóa Đơn (HoaDon) khởi tạo.
        """
        try:
            query_validate = """
                SELECT pd.MaPD, kh.TenKH
                FROM PhieuDatPhong pd
                JOIN KhachHang kh ON pd.MaKH = kh.MaKH
                WHERE pd.SoPhong = ? 
                AND kh.CCCD = ?
                AND pd.TrangThaiDat = N'Đã xác nhận' -- Chỉ check-in phiếu đã đặt trước
            """
            self.cursor.execute(query_validate, (room_id, customer_cccd))
            row = self.cursor.fetchone()
            
            if not row:
                return False, "Không tìm thấy phiếu đặt phòng hợp lệ (Sai phòng, sai CCCD hoặc chưa đặt trước)."
            
            ma_pd = row[0]
            ten_kh = row[1]

            self.cursor.execute("""
                UPDATE PhieuDatPhong 
                SET TrangThaiDat = N'Đang ở' 
                WHERE MaPD = ?
            """, (ma_pd,))

            self.cursor.execute("""
                UPDATE Phong 
                SET TrangThai = N'Đang ở' 
                WHERE SoPhong = ?
            """, (room_id,))

            self.cursor.execute("""
                INSERT INTO HoaDon (MaPD, NgayTao, TrangThaiHD)
                VALUES (?, GETDATE(), N'Chưa thanh toán')
            """, (ma_pd,))

            self.conn.commit()
            return True, f"Check-in thành công cho khách {ten_kh}. Đã khởi tạo hóa đơn."

        except Exception as e:
            self.conn.rollback()
            return False, f"Lỗi hệ thống: {str(e)}"
        
    def seed_services(self):
        """Khởi tạo dữ liệu dịch vụ mẫu"""
        services = [
            (1, 'Coca Cola', 15000), (2, 'Bia Tiger', 25000),
            (3, 'Mì tôm trứng', 30000), (4, 'Giặt ủi', 50000),
            (5, 'Massage', 200000), (6, 'Thuê xe máy', 150000)
        ]
        for sv in services:
            self.cursor.execute("""
                IF NOT EXISTS (SELECT 1 FROM DichVu WHERE MaDV=?) 
                INSERT INTO DichVu (MaDV, TenDV, Gia) VALUES (?, ?, ?)
            """, (sv[0], sv[0], sv[1], sv[2]))
        self.conn.commit()

    def get_service_list(self):
        """Lấy danh sách menu dịch vụ"""
        self.cursor.execute("SELECT * FROM DichVu")
        return [{"id": r[0], "name": r[1], "price": float(r[2])} for r in self.cursor.fetchall()]

    def add_service_usage(self, room_id, service_id, quantity):
        """
        UC2: Gọi dịch vụ [cite: 115]
        Logic: Tìm phiếu đặt phòng đang hoạt động của phòng đó -> Thêm bản ghi vào ChiTietSD
        """
        try:
            query_find_booking = """
                SELECT MaPD FROM PhieuDatPhong 
                WHERE SoPhong = ? AND TrangThaiDat = N'Đang ở'
            """
            self.cursor.execute(query_find_booking, (room_id,))
            row = self.cursor.fetchone()
            
            if not row:
                return False, "Phòng này hiện chưa có khách check-in (hoặc đang trống)."
            
            ma_pd = row[0]

            self.cursor.execute("""
                INSERT INTO ChiTietSD (MaPD, MaDV, SoLuong)
                VALUES (?, ?, ?)
            """, (ma_pd, service_id, quantity))
            
            
            self.conn.commit()
            return True, "Đã thêm dịch vụ thành công."

        except Exception as e:
            self.conn.rollback()
            return False, str(e)

    def get_bill_info(self, room_id):
        """
        Lấy toàn bộ dữ liệu thô cần thiết để tính hóa đơn (Room + Services).
        Logic tính toán sẽ thực hiện ở tầng Ứng dụng (Python) thay vì SQL.
        """
        try:
            query_room = """
                SELECT hd.MaHD, hd.NgayTao, lp.GiaTheoGio, lp.TenLP, kh.TenKH, pd.MaPD
                FROM HoaDon hd
                JOIN PhieuDatPhong pd ON hd.MaPD = pd.MaPD
                JOIN Phong p ON pd.SoPhong = p.SoPhong
                JOIN LoaiPhong lp ON p.MaLP = lp.MaLP
                JOIN KhachHang kh ON pd.MaKH = kh.MaKH
                WHERE p.SoPhong = ? 
                AND p.TrangThai = N'Đang ở' 
                AND hd.TrangThaiHD = N'Chưa thanh toán'
            """
            self.cursor.execute(query_room, (room_id,))
            room_data = self.cursor.fetchone()
            
            if not room_data:
                return None, "Không tìm thấy thông tin check-in của phòng này."

            bill_data = {
                "ma_hd": room_data[0],
                "check_in_time": room_data[1],
                "price_per_hour": float(room_data[2]),
                "room_type": room_data[3],
                "customer_name": room_data[4],
                "ma_pd": room_data[5],
                "services": []
            }

            query_services = """
                SELECT dv.TenDV, ctsd.SoLuong, dv.Gia, ctsd.ThoiGian
                FROM ChiTietSD ctsd
                JOIN DichVu dv ON ctsd.MaDV = dv.MaDV
                WHERE ctsd.MaPD = ?
            """
            self.cursor.execute(query_services, (bill_data['ma_pd'],))
            
            for row in self.cursor.fetchall():
                bill_data['services'].append({
                    "name": row[0],
                    "qty": row[1],
                    "price": float(row[2]),
                    "time": row[3]
                })

            return bill_data, "OK"

        except Exception as e:
            return None, str(e)

    def process_checkout(self, room_id, total_amount):
        """
        UC3: Check-out & Thanh toán 
        Transaction: Update Hóa đơn -> Update Phòng -> Update Phiếu
        """
        try:
            data, msg = self.get_bill_info(room_id)
            if not data: return False, msg
            
            ma_hd = data['ma_hd']
            ma_pd = data['ma_pd']

            self.cursor.execute("""
                UPDATE HoaDon 
                SET TongTien = ?, TrangThaiHD = N'Đã thanh toán' 
                WHERE MaHD = ?
            """, (total_amount, ma_hd))

            self.cursor.execute("""
                UPDATE Phong 
                SET TrangThai = N'Đang dọn' 
                WHERE SoPhong = ?
            """, (room_id,))

            self.cursor.execute("""
                UPDATE PhieuDatPhong 
                SET TrangThaiDat = N'Hoàn tất' 
                WHERE MaPD = ?
            """, (ma_pd,))

            self.conn.commit()
            return True, "Thanh toán thành công. Phòng chuyển sang trạng thái 'Đang dọn'."

        except Exception as e:
            self.conn.rollback()
            return False, str(e)
        

    def update_room_status(self, room_id, new_status):
        """
        Cho phép lễ tân/buồng phòng cập nhật thủ công trạng thái.
        VD: Dọn xong -> Set về 'Trống'. Hỏng thiết bị -> Set về 'Bảo trì'.
        """
        try:
            # Kiểm tra phòng tồn tại
            self.cursor.execute("SELECT TrangThai FROM Phong WHERE SoPhong = ?", (room_id,))
            row = self.cursor.fetchone()
            if not row:
                return "Phòng không tồn tại."
            
            old_status = row[0]

            if old_status == 'Đang ở' and new_status == 'Trống':
                return "CẢNH BÁO: Phòng đang có khách. Vui lòng thực hiện Check-out trước khi chuyển trạng thái."

            self.cursor.execute("UPDATE Phong SET TrangThai = ? WHERE SoPhong = ?", (new_status, room_id))
            self.conn.commit()
            
            return f"Cập nhật thành công: Phòng {room_id} ({old_status} -> {new_status})"

        except Exception as e:
            self.conn.rollback()
            return f"Lỗi: {str(e)}"