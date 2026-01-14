#  Hotel Management System (Hệ thống Quản lý Khách sạn)

Một ứng dụng Desktop quản lý khách sạn toàn diện được xây dựng bằng **Python (Tkinter)** và **SQL Server**. Dự án được thiết kế theo **Kiến trúc phân lớp (Layered Architecture)**, tách biệt rõ ràng giữa giao diện, nghiệp vụ và dữ liệu. Đặc biệt, hệ thống tích hợp các **Cấu trúc dữ liệu & Giải thuật** nâng cao để tối ưu hóa hiệu năng xử lý với quy mô dữ liệu lớn (2000+ phòng).
Lê Quý Thành - 20230067
Đại học Bách Khoa Hà Nội

---

##  Tính năng nổi bật

### 1.  Dashboard (Sơ đồ phòng thời gian thực)
* **Trực quan hóa trạng thái:** Hiển thị lưới phòng với màu sắc trực quan (🟢 Trống, 🔴 Đang ở, 🟡 Đang dọn/Bảo trì).
* **Bộ lọc & Tìm kiếm:**
  * Lọc theo Trạng thái, Loại phòng.
  * Tìm kiếm theo số phòng (Hỗ trợ tìm kiếm chuỗi con).
  * **Sắp xếp:** Sắp xếp danh sách hiển thị theo ID hoặc Giá tiền (Sử dụng thuật toán **Merge Sort**).

### 2.  Quản lý Đặt phòng (Booking System)
* **Kiểm tra phòng trống:** Xác định chính xác phòng trống trong khoảng thời gian bất kỳ (Sử dụng **Hash Map & Set** để tối ưu tốc độ $O(N)$).
* **Chế độ chọn phòng thông minh:**
  * **Tự động (Auto-Allocation):** Tự động đề xuất các phòng **liền kề nhau** cho khách đoàn (Sử dụng thuật toán **Sliding Window**).
  * **Thủ công (Manual Selection):** Cho phép người dùng chọn đích danh phòng mong muốn. Hỗ trợ kiểm tra nhanh ID phòng trong danh sách (Sử dụng **Binary Search**).

### 3.  Nghiệp vụ Lễ tân & Buồng phòng
* **Check-in:** Quản lý thông tin khách hàng (CCCD, SĐT), kiểm tra lịch sử khách quen.
* **Dịch vụ:** Thêm dịch vụ (Ăn uống, Giặt ủi, Spa...) vào phòng đang thuê.
* **Ghi chú & Sự cố:**
  * Cho phép ghi lại tình trạng phòng (hỏng hóc, mất đồ, bẩn...) ngay trên hệ thống.
  * Tự động hiển thị ghi chú khi thanh toán để nhắc nhở phụ thu/phạt.
* **Check-out:** Tự động tính toán tiền phòng + dịch vụ + phụ thu. 

### 4.  Tích hợp Thuật toán 
Dự án áp dụng các giải thuật kinh điển để giải quyết bài toán hiệu năng:
* **Merge Sort ($O(N \log N)$):** Sắp xếp danh sách phòng ổn định và hiệu quả.
* **Binary Search ($O(\log N)$):** Tra cứu nhanh sự tồn tại của phòng trong danh sách lớn.
* **Sliding Window ($O(N)$):** Giải quyết bài toán xếp phòng liền kề tối ưu chỉ với 1 vòng lặp.
* **Backtracking ($O(2^N)$):** Gợi ý combo dịch vụ phù hợp ngân sách (Biến thể bài toán Knapsack).

---

##  Cài đặt & Hướng dẫn sử dụng

### Yêu cầu hệ thống
* **Python 3.x**
* **SQL Server** (Bản Express hoặc Developer)
* **ODBC Driver 17 for SQL Server**

### Bước 1: Clone dự án
```bash
git clone https://github.com/ThanhQuy78/Project-I.git
cd Project-I
```

### Bước 2: Cài đặt thư viện
```bash
pip install pyodbc
```

### Bước 3: Cấu hình Database
Mở file database.py và chỉnh sửa thông tin kết nối phù hợp 
```bash
class DatabaseConfig:
    SERVER = '.\\SQLEXPRESS'  # Tên Server SQL của bạn
    DATABASE = 'HotelManagementDB'
```
Nếu Database chưa được tạo sẵn hay đã tạo nhưng chưa thêm dữ liệu, hệ thống có thể tự động sinh dữ liệu ngẫu nhiên

### Bước 4: Chạy ứng dụng
```bash
python gui.py
```

### Bước 5(Optional): Chạy so sánh các giải thuật
```bash
python benchmark.py
```

## Kiến trúc dự án
```text
├── gui.py               # Presentation Layer: Giao diện Tkinter, xử lý sự kiện
├── services.py          # Business Logic Layer: Chứa class HotelAlgorithms (Logic thuật toán)
├── repositories.py      # Data Access Layer: Truy vấn SQL, CRUD
├── models.py            # DTOs: Các class đại diện dữ liệu (Room, BillDetail...)
├── database.py          # Infrastructure: Kết nối DB và khởi tạo dữ liệu mẫu
└── benchmark.py         # Testing: Script đo lường hiệu năng giải thuật
```

## Thiết kế Cơ sở dữ liệu 
* **Phong**: SoPhong (PK), TrangThai, MaLP, GhiChu.

* **LoaiPhong**: MaLP (PK), TenLP, GiaTheoNgay, SucChua.

* **KhachHang**: MaKH (PK), TenKH, CCCD (Unique), SDT.

* **PhieuDatPhong**: MaPD (PK), NgayDen, NgayDi.

* **HoaDon**: MaHD (PK), TongTien, PhuThu, TrangThai.

* **DichVu** MaDV (PK), TenDV, Gia.
  
* **ChiTietSD**: MaSD (PK), SoLuong, ThoiGian.
