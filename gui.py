import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime

from database import DatabaseManager
from repositories import RoomRepository, ServiceRepository, OperationRepository
from services import HotelAlgorithms

class HotelApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Hệ thống Quản lý Khách Sạn (GUI)")
        self.geometry("1200x800")
        
        self.init_db()
        
        self.setup_styles()

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # --- TAB 1: DASHBOARD  ---
        self.tab_dashboard = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_dashboard, text=" Sơ đồ & Quản lý Phòng")
        self.setup_dashboard_tab()

        # --- TAB 2: ĐẶT PHÒNG  ---
        self.tab_booking = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_booking, text=" Đặt Phòng")
        self.setup_booking_tab()

        # --- TAB 3: CHECK-IN ---
        self.tab_checkin = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_checkin, text=" Check-in")
        self.setup_checkin_tab()

    def init_db(self):
        try:
            db = DatabaseManager()
            conn = db.get_connection()
            self.room_repo = RoomRepository(conn.cursor())
            self.op_repo = OperationRepository(conn)
            self.svc_repo = ServiceRepository(conn.cursor())
        except Exception as e:
            messagebox.showerror("Lỗi DB", f"Không thể kết nối Database: {e}")

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Room.TButton', font=('Arial', 10, 'bold'), width=10, height=4)
        style.map('Room.TButton', background=[('active', '#e1e1e1')])


    def setup_dashboard_tab(self):
        search_frame = ttk.LabelFrame(self.tab_dashboard, text="🔍 Bộ lọc tìm kiếm")
        search_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(search_frame, text="Số phòng:").pack(side='left', padx=5)
        self.var_search_id = tk.StringVar()
        entry_id = ttk.Entry(search_frame, textvariable=self.var_search_id, width=10)
        entry_id.pack(side='left', padx=5)
        entry_id.bind('<Return>', lambda e: self.refresh_dashboard()) 

        ttk.Label(search_frame, text="Loại phòng:").pack(side='left', padx=5)
        self.cb_search_type = ttk.Combobox(search_frame, state="readonly", width=15)
        self.cb_search_type.pack(side='left', padx=5)

        self.cb_search_type['values'] = ["Tất cả", "Standard", "Superior", "Deluxe", "Family", "President"]
        self.cb_search_type.current(0)

        ttk.Label(search_frame, text="Trạng thái:").pack(side='left', padx=5)
        self.cb_search_status = ttk.Combobox(search_frame, state="readonly", width=15)
        self.cb_search_status['values'] = ["Tất cả", "Trống", "Đang ở", "Đang dọn", "Bảo trì"]
        self.cb_search_status.current(0)
        self.cb_search_status.pack(side='left', padx=5)

        ttk.Button(search_frame, text="Tìm kiếm", command=self.refresh_dashboard).pack(side='left', padx=10)
        ttk.Button(search_frame, text="Xóa bộ lọc", command=self.reset_filters).pack(side='left')

        toolbar = ttk.Frame(self.tab_dashboard)
        toolbar.pack(fill='x', padx=10, pady=5)
        def legend(parent, color, text):
            f = tk.Frame(parent)
            tk.Label(f, bg=color, width=2, height=1).pack(side='left', padx=2)
            tk.Label(f, text=text).pack(side='left')
            return f

        legend(toolbar, "#4CAF50", "Trống").pack(side='right', padx=5)
        legend(toolbar, "#F44336", "Đang ở").pack(side='right', padx=5)
        legend(toolbar, "#FF9800", "Bảo trì / Dọn").pack(side='right', padx=5)



        container = ttk.Frame(self.tab_dashboard)
        container.pack(fill='both', expand=True, padx=10, pady=5)
        
        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.canvas_frame = ttk.Frame(canvas)

        self.canvas_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.canvas_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.refresh_dashboard()

    def reset_filters(self):
        """Đặt lại bộ lọc về mặc định"""
        self.var_search_id.set("")
        self.cb_search_type.current(0)
        self.cb_search_status.current(0)
        self.refresh_dashboard()

    def refresh_dashboard(self):
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()

        all_rooms = self.room_repo.get_all()
        
        search_id = self.var_search_id.get().strip()
        search_type = self.cb_search_type.get()
        search_status = self.cb_search_status.get()

        filtered_rooms = []
        for r in all_rooms:
            if search_id and search_id not in str(r.id):
                continue
            
            if search_type != "Tất cả" and r.type_name != search_type:
                continue
            
            if search_status != "Tất cả" and r.status != search_status:
                continue
            
            filtered_rooms.append(r)

        filtered_rooms = HotelAlgorithms.merge_sort(filtered_rooms, key=lambda r: r.id)
        
        color_map = {
            'Trống': '#4CAF50',     
            'Đang ở': '#F44336',    
            'Bảo trì': '#FF9800',   
            'Đang dọn': '#FFC107'   
        }

        columns = 8 
        if not filtered_rooms:
            ttk.Label(self.canvas_frame, text="Không tìm thấy phòng nào phù hợp!", font=("Arial", 12)).pack(pady=20)
            return

        for i, r in enumerate(filtered_rooms):
            bg_color = color_map.get(r.status, '#9E9E9E')
            
            btn = tk.Button(
                self.canvas_frame, 
                text=f"P{r.id}\n{r.type_name}\n({r.status})",
                bg=bg_color, fg='white', font=('Arial', 9, 'bold'),
                width=12, height=4,
                command=lambda room=r: self.open_room_detail(room)
            )
            btn.grid(row=i//columns, column=i%columns, padx=5, pady=5)

    def open_room_detail(self, room):
        """Hàm xử lý khi click vào một phòng (Có Ghi chú & Phụ thu)"""
        popup = tk.Toplevel(self)
        popup.title(f"Quản lý Phòng {room.id}")
        popup.geometry("600x700") 


        info_frame = ttk.LabelFrame(popup, text="Thông tin chung")
        info_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(info_frame, text=f"Số phòng: {room.id}").grid(row=0, column=0, sticky='w', padx=10, pady=2)
        ttk.Label(info_frame, text=f"Loại phòng: {room.type_name}").grid(row=0, column=1, sticky='w', padx=10, pady=2)
        ttk.Label(info_frame, text=f"Giá niêm yết: {room.price:,.0f} VND/ngày").grid(row=1, column=0, sticky='w', padx=10, pady=2)
        ttk.Label(info_frame, text=f"Trạng thái: {room.status}").grid(row=1, column=1, sticky='w', padx=10, pady=2)


        note_frame = ttk.LabelFrame(popup, text=" Ghi chú & Tình trạng tài sản")
        note_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        txt_note = tk.Text(note_frame, height=4, width=50, font=("Arial", 10))
        txt_note.pack(padx=5, pady=5, fill='both', expand=True)
        
        current_note = getattr(room, 'note', '') 
        txt_note.insert(tk.END, current_note)
        
        def save_note_action():
            new_note = txt_note.get("1.0", tk.END).strip()
            
            ok, msg = self.room_repo.update_note(room.id, new_note)
            
            if ok:
                messagebox.showinfo("Đã lưu", "Cập nhật ghi chú thành công!", parent=popup)
            else:
                messagebox.showerror("Lỗi", msg, parent=popup)

        btn_save = ttk.Button(note_frame, text=" Lưu Ghi Chú", command=save_note_action)
        btn_save.pack(anchor='e', padx=5, pady=5)

        action_frame = ttk.LabelFrame(popup, text="Chức năng quản lý")
        action_frame.pack(fill='x', padx=10, pady=10)

        if room.status in ['Đang ở']:
            raw_data, msg = self.op_repo.get_bill_raw_data(room.id)
            if raw_data:
                bill = HotelAlgorithms.calculate_bill(raw_data)
                
                lbl_cust = ttk.Label(action_frame, text=f"Khách: {bill.customer_name} | Vào: {bill.check_in.strftime('%d/%m %H:%M')} | Ở: {bill.days_used} ngày", foreground="blue")
                lbl_cust.pack(pady=5)
                
                btn_frame = ttk.Frame(action_frame)
                btn_frame.pack(pady=10)
                
                ttk.Button(btn_frame, text=" Thêm Dịch Vụ", 
                           command=lambda: self.add_service_ui(room.id, popup)).grid(row=0, column=0, padx=5)
                
                ttk.Button(btn_frame, text=" Xem Hóa Đơn Tạm", 
                           command=lambda: self.show_bill_ui(room.id, "Tạm tính", popup)).grid(row=0, column=1, padx=5)
                
                ttk.Button(btn_frame, text=" Check-out & Thanh Toán", 
                           command=lambda: self.checkout_ui(room.id, popup, txt_note.get("1.0", tk.END).strip())).grid(row=0, column=2, padx=5)

        else:
            ttk.Label(action_frame, text="Cập nhật trạng thái thủ công:").pack(pady=5)
            
            btn_st_frame = ttk.Frame(action_frame)
            btn_st_frame.pack(pady=5)
            
            states = ["Trống", "Đang dọn", "Bảo trì"]
            for st in states:
                if st != room.status:
                    ttk.Button(
                        btn_st_frame, text=f"-> {st}", 
                        command=lambda s=st: self.update_status(room.id, s, popup)
                    ).pack(side='left', padx=5)

    def update_status(self, rid, new_status, popup):
        ok, msg = self.room_repo.update_status(rid, new_status)
        if ok:
            messagebox.showinfo("Thành công", msg)
            popup.destroy()
            self.refresh_dashboard()
        else:
            messagebox.showerror("Lỗi", msg)


    def show_bill_ui(self, rid, title, parent_window=None):
        raw, msg = self.op_repo.get_bill_raw_data(rid)
        
        if not raw:
            messagebox.showerror("Lỗi", msg, parent=parent_window)
            return None
        bill = HotelAlgorithms.calculate_bill(raw)
        
        bill_text = f"""
        === {title.upper()} ===
        Khách hàng: {bill.customer_name}
        Check-in:   {bill.check_in.strftime('%Y-%m-%d %H:%M')}
        --------------------------------
        1. Tiền phòng:
           {bill.room_price:,.0f} x {bill.days_used} ngày = {bill.room_total:,.0f}
           
        2. Dịch vụ:
           Tổng cộng: {bill.service_total:,.0f}
        """
        
        if bill.service_items:
            bill_text += "\n   Chi tiết dịch vụ:"
            for s in bill.service_items:
                bill_text += f"\n   - {s['name']} (x{s['qty']}): {s['qty']*s['price']:,.0f}"
        else:
            bill_text += "\n   (Không sử dụng dịch vụ)"
            
        bill_text += f"\n--------------------------------\n TỔNG CỘNG: {bill.grand_total:,.0f} VND"
        
        if title == "Tạm tính":
            messagebox.showinfo(title, bill_text, parent=parent_window)
            
        return bill

    def checkout_ui(self, rid, parent_popup, current_note =""):
        bill = self.show_bill_ui(rid, "Kiểm tra trước thanh toán", parent_popup)
        if not bill: return

        pay_window = tk.Toplevel(self)
        pay_window.title(f"Thanh toán Phòng {rid}")
        pay_window.geometry("400x500")
        pay_window.transient(parent_popup)
        pay_window.grab_set()

        ttk.Label(pay_window, text="XÁC NHẬN THANH TOÁN", font=("Arial", 14, "bold")).pack(pady=15)

        frame_sum = ttk.Frame(pay_window)
        frame_sum.pack(fill='x', padx=30)
        
        ttk.Label(frame_sum, text="Tiền phòng:").grid(row=0, column=0, sticky='w')
        ttk.Label(frame_sum, text=f"{bill.room_total:,.0f}").grid(row=0, column=1, sticky='e')
        
        ttk.Label(frame_sum, text="Dịch vụ:").grid(row=1, column=0, sticky='w')
        ttk.Label(frame_sum, text=f"{bill.service_total:,.0f}").grid(row=1, column=1, sticky='e')
        
        ttk.Separator(pay_window, orient='horizontal').pack(fill='x', padx=20, pady=10)

        if current_note:
            ttk.Label(pay_window, text=" Lưu ý (Ghi chú phòng):", foreground="red").pack(anchor='w', padx=30)
            lbl_note = tk.Label(pay_window, text=current_note, fg="#555", wraplength=340, justify="left", bg="#fff3cd", padx=5, pady=5)
            lbl_note.pack(anchor='w', padx=30, pady=5, fill='x')
        else:
            ttk.Label(pay_window, text="(Không có ghi chú đặc biệt)", foreground="gray").pack(pady=5)

        ttk.Label(pay_window, text="Phụ thu / Phạt (VND):").pack(pady=(10,0))
        entry_surcharge = ttk.Entry(pay_window, font=("Arial", 11))
        entry_surcharge.pack(pady=5)
        entry_surcharge.insert(0, "0")

        def confirm_pay():
            try:
                surcharge_str = entry_surcharge.get()
                if not surcharge_str: surcharge_str = "0"
                surcharge = float(surcharge_str)
                
                final_total = bill.grand_total + surcharge
                
                msg = f"Tổng bill: {bill.grand_total:,.0f}\nPhụ thu: {surcharge:,.0f}\n\nKHÁCH CẦN TRẢ: {final_total:,.0f} VND"
                
                if messagebox.askyesno("Chốt thanh toán", msg, parent=pay_window):
                    ok, res_msg = self.op_repo.checkout(rid, bill, surcharge)
                    
                    if ok:
                        messagebox.showinfo("Thành công", res_msg, parent=parent_popup)
                        pay_window.destroy()
                        parent_popup.destroy()
                        self.refresh_dashboard() 
                    else:
                        messagebox.showerror("Lỗi", res_msg, parent=pay_window)
            except ValueError:
                messagebox.showerror("Lỗi", "Số tiền phụ thu không hợp lệ", parent=pay_window)

        ttk.Button(pay_window, text=" THANH TOÁN & TRẢ PHÒNG", command=confirm_pay).pack(pady=20, ipadx=10, ipady=5)


    selected_manual_rooms = [] 

    def setup_booking_tab(self):
        frame = ttk.Frame(self.tab_booking)
        frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        grp_search = ttk.LabelFrame(frame, text="1. Tìm kiếm phòng trống")
        grp_search.pack(fill='x', pady=10)
        
        ttk.Label(grp_search, text="Ngày đến:").grid(row=0, column=0, padx=5)
        self.bk_entry_start = ttk.Entry(grp_search); self.bk_entry_start.grid(row=0, column=1)
        self.bk_entry_start.insert(0, datetime.now().strftime("%Y-%m-%d"))

        ttk.Label(grp_search, text="Ngày đi:").grid(row=0, column=2, padx=5)
        self.bk_entry_end = ttk.Entry(grp_search); self.bk_entry_end.grid(row=0, column=3)
        
        ttk.Button(grp_search, text=" Tìm kiếm", command=self.bk_search).grid(row=0, column=4, padx=20)
        
        ttk.Label(frame, text="* Double click vào dòng để chọn phòng thủ công (Merge Sort/Binary Search)", font=("Arial", 9, "italic"), foreground="gray").pack(anchor='w')
        ttk.Label(frame, text="* Hoặc nhập số lượng bên dưới để hệ thống tự chọn phòng gần nhau (Sliding Window)", font=("Arial", 9, "italic"), foreground="gray").pack(anchor='w')
        
        self.bk_tree = ttk.Treeview(frame, columns=("ID", "Loại", "Giá", "Còn Trống"), show='headings', height=6)
        for col in ("ID", "Loại", "Giá", "Còn Trống"):
            self.bk_tree.heading(col, text=col)
        self.bk_tree.pack(fill='x', pady=5)
        
        self.bk_tree.bind("<Double-1>", self.open_manual_selection_popup)
        
        grp_form = ttk.LabelFrame(frame, text="2. Thông tin đặt phòng")
        grp_form.pack(fill='x', pady=10)
        
        self.lbl_selected_rooms = ttk.Label(grp_form, text="Chưa chọn thủ công (Sẽ dùng chế độ tự động)", foreground="blue")
        self.lbl_selected_rooms.grid(row=0, column=0, columnspan=4, pady=5)

        ttk.Label(grp_form, text="Họ tên:").grid(row=1, column=0, sticky='e', padx=5)
        self.bk_name = ttk.Entry(grp_form); self.bk_name.grid(row=1, column=1, sticky='w')
        
        ttk.Label(grp_form, text="CCCD:").grid(row=1, column=2, sticky='e', padx=5)
        self.bk_cccd = ttk.Entry(grp_form); self.bk_cccd.grid(row=1, column=3, sticky='w')
        
        ttk.Label(grp_form, text="SĐT:").grid(row=2, column=0, sticky='e', padx=5)
        self.bk_phone = ttk.Entry(grp_form); self.bk_phone.grid(row=2, column=1, sticky='w')
        
        ttk.Label(grp_form, text="Số lượng phòng:").grid(row=2, column=2, sticky='e', padx=5)
        self.bk_qty = ttk.Entry(grp_form, width=5); self.bk_qty.grid(row=2, column=3, sticky='w')
        self.bk_qty.insert(0, "1") 
        
        ttk.Button(grp_form, text="XÁC NHẬN ĐẶT PHÒNG", command=self.bk_confirm).grid(row=3, column=0, columnspan=4, pady=20)

    def bk_search(self):
        self.selected_manual_rooms = []
        self.lbl_selected_rooms.config(text="Chưa chọn phòng nào (Sẽ tự động chọn)", foreground="blue")
        
        s_date = self.bk_entry_start.get()
        e_date = self.bk_entry_end.get()
        
        try:
            all_rooms = self.room_repo.get_all()
            busy_ids = self.room_repo.get_conflict_ids(s_date, e_date)
            
            self.bk_stats = HotelAlgorithms.analyze_availability(all_rooms, busy_ids)
            
            self.bk_stats.sort(key=lambda x: x['id'])
            
            for row in self.bk_tree.get_children():
                self.bk_tree.delete(row)
            
            for st in self.bk_stats:
                self.bk_tree.insert("", "end", values=(st['id'], st['name'], f"{st['price']:,.0f}", st['count']))
                
        except Exception as e:
            messagebox.showerror("Lỗi hệ thống", f"Chi tiết lỗi: {str(e)}")


    def open_manual_selection_popup(self, event):
        sel = self.bk_tree.selection()
        if not sel: return
        
        item = self.bk_tree.item(sel[0])
        type_id = item['values'][0]
        type_name = item['values'][1]
        
        target_stat = next((x for x in self.bk_stats if x['id'] == type_id), None)
        
        if not target_stat or not target_stat['room_ids']:
            messagebox.showinfo("Thông báo", "Loại phòng này đã hết chỗ!")
            return

        raw_ids = target_stat['room_ids']
        sorted_ids = HotelAlgorithms.merge_sort(raw_ids)

        popup = tk.Toplevel(self)
        popup.title(f"Chọn phòng {type_name}")
        popup.geometry("500x600")
        
        frame_search = ttk.LabelFrame(popup, text="Kiểm tra phòng trống (Binary Search)")
        frame_search.pack(fill='x', padx=10, pady=5)
        
        entry_check = ttk.Entry(frame_search)
        entry_check.pack(side='left', padx=5)
        
        def check_availability():
            try:
                val = int(entry_check.get())
                found = HotelAlgorithms.binary_search_int(sorted_ids, val)
                if found:
                    messagebox.showinfo("Kết quả", f"Phòng {val} ĐANG TRỐNG! Có thể chọn.", parent=popup)
                else:
                    messagebox.showwarning("Kết quả", f"Phòng {val} không có trong danh sách này.", parent=popup)
            except ValueError:
                messagebox.showerror("Lỗi", "Vui lòng nhập số phòng", parent=popup)
                
        ttk.Button(frame_search, text="Kiểm tra nhanh", command=check_availability).pack(side='left', padx=5)

        ttk.Label(popup, text="Danh sách phòng trống (Đã sắp xếp):").pack(pady=5)
        listbox = tk.Listbox(popup, selectmode=tk.MULTIPLE)
        listbox.pack(fill='both', expand=True, padx=10, pady=5)
        
        for rid in sorted_ids:
            listbox.insert(tk.END, f"Phòng {rid}")
            
        def confirm_selection():
            selections = listbox.curselection()
            if not selections:
                messagebox.showwarning("Chú ý", "Chưa chọn phòng nào!", parent=popup)
                return
            
            self.selected_manual_rooms = []
            for i in selections:
                self.selected_manual_rooms.append(sorted_ids[i])
            
            self.lbl_selected_rooms.config(text=f"Đã chọn thủ công: {self.selected_manual_rooms}", foreground="green")
            popup.destroy()
            
        ttk.Button(popup, text=" Xác nhận chọn", command=confirm_selection).pack(pady=10)


    def bk_confirm(self):
        guest = (self.bk_name.get(), self.bk_cccd.get(), self.bk_phone.get())
        if not all(guest):
            messagebox.showwarning("Lỗi", "Vui lòng nhập đủ thông tin khách!")
            return

        room_ids_to_book = []
        
        if self.selected_manual_rooms:
            room_ids_to_book = self.selected_manual_rooms
            
        else:
            sel = self.bk_tree.selection()
            if not sel:
                messagebox.showwarning("Lỗi", "Vui lòng chọn loại phòng!")
                return
            try:
                qty = int(self.bk_qty.get())
                if qty <= 0: raise ValueError
                
                type_id = self.bk_tree.item(sel[0])['values'][0]
                target = next((x for x in self.bk_stats if x['id'] == type_id), None)
                
                if qty > target['count']:
                    messagebox.showerror("Lỗi", "Không đủ phòng trống!")
                    return
                
                room_ids_to_book = HotelAlgorithms.find_closest_rooms(target['room_ids'], qty)
            except ValueError:
                messagebox.showerror("Lỗi", "Số lượng không hợp lệ!")
                return

        if room_ids_to_book:
            if messagebox.askyesno("Xác nhận", f"Đặt các phòng: {room_ids_to_book}?"):
                ok, msg = self.op_repo.create_booking(guest, room_ids_to_book, self.bk_entry_start.get(), self.bk_entry_end.get())
                if ok:
                    messagebox.showinfo("Thành công", msg)
                    self.bk_search() 
                else:
                    messagebox.showerror("Lỗi", msg)


    def setup_checkin_tab(self):
        frame = ttk.Frame(self.tab_checkin)
        frame.pack(fill='both', expand=True, padx=50, pady=50)
        
        ttk.Label(frame, text="CHECK-IN TỰ ĐỘNG", font=('Arial', 16, 'bold')).pack(pady=20)
        
        ttk.Label(frame, text="Nhập CCCD Khách Hàng:").pack(pady=5)
        self.ck_cccd = ttk.Entry(frame, font=('Arial', 12))
        self.ck_cccd.pack(pady=5, ipadx=50)
        
        ttk.Button(frame, text="Thực hiện Check-in", command=self.ck_process).pack(pady=20)
        
        self.ck_lbl_res = ttk.Label(frame, text="", font=('Arial', 10), foreground="blue")
        self.ck_lbl_res.pack(pady=10)

    def ck_process(self):
        cccd = self.ck_cccd.get()
        status, res = self.op_repo.check_in(cccd)
        if status:
            msg = f"Check-in thành công!\nKhách: {res['name']}\nPhòng: {res['rooms']}"
            self.ck_lbl_res.config(text=msg, foreground="green")
            messagebox.showinfo("Thành công", msg)
            self.refresh_dashboard()
        else:
            self.ck_lbl_res.config(text=res, foreground="red")
            messagebox.showwarning("Lỗi", res)

    def add_service_ui(self, rid, parent_popup = None):
        svc_popup = tk.Toplevel(self)
        svc_popup.title(f"Gọi dịch vụ - Phòng {rid}")
        svc_popup.geometry("450x650")

        if parent_popup:
            svc_popup.transient(parent_popup)
            svc_popup.grab_set()
        
        services = self.svc_repo.get_all()
        service_map = {s.name: s.id for s in services} 
        
        frame_single = ttk.LabelFrame(svc_popup, text="1. Chọn món lẻ")
        frame_single.pack(fill='x', padx=10, pady=5)
        
        listbox = tk.Listbox(frame_single, height=8)
        for s in services:
            listbox.insert(tk.END, f"{s.id}. {s.name} - {s.price:,.0f}đ")
        listbox.pack(pady=5, fill='x', padx=5)
        
        frame_qty = ttk.Frame(frame_single)
        frame_qty.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(frame_qty, text="Số lượng:").pack(side='left')
        
        var_qty = tk.StringVar(value="1")
        entry_qty = ttk.Entry(frame_qty, width=10, textvariable=var_qty)
        entry_qty.pack(side='left', padx=5)
        
        def confirm_single():
            sel = listbox.curselection()
            if not sel: 
                messagebox.showwarning("Lỗi", "Vui lòng chọn một món!")
                return
            
            sid = services[sel[0]].id
            try:
                qty = int(var_qty.get())
                if qty <= 0: raise ValueError
                
                ok, msg = self.svc_repo.add_usage(rid, sid, qty)
                
                if ok: 
                    messagebox.showinfo("Thành công", msg, parent=svc_popup)
                    svc_popup.destroy() 

                    if parent_popup:
                        parent_popup.lift()
                        parent_popup.focus_force()
                else: 
                    messagebox.showerror("Lỗi", msg)
            except ValueError: 
                messagebox.showerror("Lỗi", "Số lượng phải là số nguyên dương")

        ttk.Button(frame_qty, text="Gọi món này", command=confirm_single).pack(side='right')

        frame_combo = ttk.LabelFrame(svc_popup, text="2. Gợi ý Combo theo túi tiền")
        frame_combo.pack(fill='both', expand=True, padx=10, pady=10)
        
        frame_input = ttk.Frame(frame_combo)
        frame_input.pack(fill='x', padx=5, pady=5)
        ttk.Label(frame_input, text="Ngân sách (VND):").pack(side='left')
        entry_budget = ttk.Entry(frame_input, width=15)
        entry_budget.pack(side='left', padx=5)
        
        list_combo = tk.Listbox(frame_combo, height=8, bg="#f0f0f0")
        list_combo.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.current_combos = []

        def find_combos():
            try:
                budget = float(entry_budget.get())
                self.current_combos = HotelAlgorithms.suggest_service_combos(services, budget)
                list_combo.delete(0, tk.END)
                if not self.current_combos:
                    list_combo.insert(tk.END, "Không tìm thấy combo phù hợp!")
                    return

                for i, c in enumerate(self.current_combos, 1):
                    names = ", ".join(c['combo'])
                    list_combo.insert(tk.END, f"#{i} [{c['total']:,.0f}đ]: {names}")
            except ValueError:
                messagebox.showerror("Lỗi", "Nhập sai số tiền")

        def select_combo():
            sel = list_combo.curselection()
            if not sel or not self.current_combos: return
            
            chosen = self.current_combos[sel[0]]
            confirm = messagebox.askyesno("Xác nhận", f"Gọi Combo giá {chosen['total']:,.0f}đ?")
            if confirm:
                count = 0
                for name in chosen['combo']:
                    if name in service_map:
                        self.svc_repo.add_usage(rid, service_map[name], 1)
                        count += 1
                
                messagebox.showinfo("Hoàn tất", f"Đã thêm {count} món.")
                svc_popup.destroy()

                if parent_popup:
                    parent_popup.lift()
                    parent_popup.focus_force()

        btn_frame = ttk.Frame(frame_combo)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text=" Tìm Combo", command=find_combos).pack(side='left', padx=10)
        ttk.Button(btn_frame, text=" Chọn Combo", command=select_combo).pack(side='left', padx=10)

if __name__ == "__main__":
    app = HotelApp()
    app.mainloop()