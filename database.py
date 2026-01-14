import pyodbc
import random

class DatabaseConfig:
    # LƯU Ý: Sửa lại tên SERVER nếu cần thiết
    SERVER = '.\\SQLEXPRESS' 
    DATABASE = 'HotelManagementDB'
    DRIVER = '{ODBC Driver 17 for SQL Server}'
    CONN_STR = f'DRIVER={DRIVER};SERVER={SERVER};DATABASE={DATABASE};Trusted_Connection=yes;'

class DatabaseManager:
    def __init__(self):
        self._ensure_db_exists()
        self.conn = pyodbc.connect(DatabaseConfig.CONN_STR)
        self.cursor = self.conn.cursor()
        self._init_tables()
        self.seed_data()

    def get_connection(self):
        return self.conn

    def _ensure_db_exists(self):
        try:
            # Kết nối vào master để check DB
            master_str = f'DRIVER={DatabaseConfig.DRIVER};SERVER={DatabaseConfig.SERVER};Trusted_Connection=yes;AutoCommit=True;'
            cnxn = pyodbc.connect(master_str, autocommit=True)
            crsr = cnxn.cursor()
            crsr.execute(f"SELECT name FROM master.dbo.sysdatabases WHERE name = '{DatabaseConfig.DATABASE}'")
            if not crsr.fetchone():
                print(f"[SYSTEM] Creating Database '{DatabaseConfig.DATABASE}'...")
                crsr.execute(f"CREATE DATABASE {DatabaseConfig.DATABASE}")
            cnxn.close()
        except Exception as e:
            print(f"[FATAL] Connection Error: {e}")
            exit()

    def _init_tables(self):
        self.cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='KhachHang' AND xtype='U')
            CREATE TABLE KhachHang (
                MaKH INT IDENTITY(1,1) PRIMARY KEY, 
                TenKH NVARCHAR(100), 
                CCCD NVARCHAR(20) UNIQUE, -- <--- Ràng buộc duy nhất
                SDT NVARCHAR(15)
            )
        """)
        
        self.cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='LoaiPhong' AND xtype='U')
            CREATE TABLE LoaiPhong (MaLP INT PRIMARY KEY, TenLP NVARCHAR(50), GiaTheoNgay DECIMAL(18, 0), SucChua INT DEFAULT 2)
        """)
        self.cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Phong' AND xtype='U')
            CREATE TABLE Phong (SoPhong INT PRIMARY KEY, TrangThai NVARCHAR(50), MaLP INT, GhiChu NVARCHAR(500) DEFAULT N'', FOREIGN KEY(MaLP) REFERENCES LoaiPhong(MaLP))
        """)
        self.cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='PhieuDatPhong' AND xtype='U')
            CREATE TABLE PhieuDatPhong (MaPD INT IDENTITY(1,1) PRIMARY KEY, MaKH INT, SoPhong INT, NgayDen DATE, NgayDi DATE, TrangThaiDat NVARCHAR(50), FOREIGN KEY(MaKH) REFERENCES KhachHang(MaKH), FOREIGN KEY(SoPhong) REFERENCES Phong(SoPhong))
        """)
        self.cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='HoaDon' AND xtype='U')
            CREATE TABLE HoaDon (MaHD INT IDENTITY(1,1) PRIMARY KEY, NgayTao DATETIME DEFAULT GETDATE(), MaPD INT, TongTien DECIMAL(18, 0) DEFAULT 0, PhuThu DECIMAL(18, 0) DEFAULT 0, TrangThaiHD NVARCHAR(50) DEFAULT N'Chưa thanh toán', FOREIGN KEY(MaPD) REFERENCES PhieuDatPhong(MaPD))
        """)
        self.cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='DichVu' AND xtype='U')
            CREATE TABLE DichVu (MaDV INT PRIMARY KEY, TenDV NVARCHAR(50), Gia DECIMAL(18, 0))
        """)
        self.cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='ChiTietSD' AND xtype='U')
            CREATE TABLE ChiTietSD (MaSD INT IDENTITY(1,1) PRIMARY KEY, MaPD INT, MaDV INT, SoLuong INT, ThoiGian DATETIME DEFAULT GETDATE(), FOREIGN KEY(MaPD) REFERENCES PhieuDatPhong(MaPD), FOREIGN KEY(MaDV) REFERENCES DichVu(MaDV))
        """)
        self.conn.commit()

    def seed_data(self):
        # Seed Loai Phong
        loai_phongs = [(1, 'Standard', 300000, 2), (2, 'Superior', 500000, 2), (3, 'Deluxe', 800000, 2), (4, 'Family', 1200000, 4), (5, 'President', 3000000, 4)]
        for lp in loai_phongs:
            params = (lp[0],) + lp
            self.cursor.execute("IF NOT EXISTS (SELECT 1 FROM LoaiPhong WHERE MaLP=?) INSERT INTO LoaiPhong VALUES (?,?,?,?)", params)
        
        # Seed Phong (2000 phong)
        self.cursor.execute("SELECT COUNT(*) FROM Phong")
        if self.cursor.fetchone()[0] == 0:
            print("[SYSTEM] Seeding 2000 rooms...")
            batch_data = []
            statuses = ['Trống', 'Đang ở', 'Đang dọn', 'Bảo trì']
            for i in range(101, 2101):
                batch_data.append((i, 'Trống', random.randint(1, 5), ''))

            query = "INSERT INTO Phong (SoPhong, TrangThai, MaLP, GhiChu) VALUES (?, ?, ?, ?)"
            for i in range(0, len(batch_data), 500):
                self.cursor.executemany(query, batch_data[i:i+500])
            self.conn.commit()

        # Seed Services
        services = [(1, 'Coca Cola', 15000), (2, 'Bia Tiger', 25000), (3, 'Mì tôm trứng', 30000), (4, 'Giặt ủi', 50000), (5, 'Massage', 200000), (6, 'Thuê xe máy', 150000)]
        for sv in services:
             params = (sv[0],) + sv
             self.cursor.execute("IF NOT EXISTS (SELECT 1 FROM DichVu WHERE MaDV=?) INSERT INTO DichVu (MaDV, TenDV, Gia) VALUES (?, ?, ?)", params)
        self.conn.commit()