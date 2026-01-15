import math
from datetime import datetime
from models import BillDetail

class HotelAlgorithms:
    
    @staticmethod
    def analyze_availability(all_rooms, conflict_ids):
        """Logic lọc phòng bằng Hash Map"""
        busy_set = set(conflict_ids)
        stats_map = {} 
        for room in all_rooms:
            if room.id not in busy_set and room.status != 'Bảo trì':
                tid = room.type_id
                if tid not in stats_map:
                    stats_map[tid] = {
                        "id": tid, "name": room.type_name, 
                        "price": room.price, "cap": room.capacity,
                        "count": 0, "room_ids": []
                    }
                stats_map[tid]["count"] += 1
                stats_map[tid]["room_ids"].append(room.id)
        return list(stats_map.values())
    

    @staticmethod
    def merge_sort(arr, key=lambda x: x):
        if len(arr) <= 1: return arr
        
        mid = len(arr) // 2
        left = HotelAlgorithms.merge_sort(arr[:mid], key=key)
        right = HotelAlgorithms.merge_sort(arr[mid:], key=key)
        
        res = []
        i = j = 0
        while i < len(left) and j < len(right):
            if key(left[i]) <= key(right[j]):
                res.append(left[i]); i += 1
            else: 
                res.append(right[j]); j += 1
        
        res.extend(left[i:]); res.extend(right[j:])
        return res

    
    @staticmethod
    def binary_search_int(sorted_arr, target):
        low, high = 0, len(sorted_arr) - 1
        while low <= high:
            mid = (low + high) // 2
            if sorted_arr[mid] == target:
                return True 
            elif sorted_arr[mid] < target:
                low = mid + 1
            else:
                high = mid - 1
        return False 

    @staticmethod
    def calculate_bill(raw_data):
        """Logic tính tiền (Pure Function)"""
        check_out = datetime.now()
        check_in = raw_data['check_in']

        days = math.ceil((check_out - check_in).total_seconds() / 86400)
        days = max(1, days)

        room_total = days * raw_data['price']
        svc_total = sum(s['qty'] * s['price'] for s in raw_data['services'])
        
        return BillDetail(
            ma_hd=raw_data['ma_hd'], ma_pd=raw_data['ma_pd'],
            customer_name=raw_data['customer'],
            check_in=check_in, check_out=check_out, days_used=days,
            room_price=raw_data['price'], room_total=room_total,
            service_items=raw_data['services'], service_total=svc_total,
            grand_total=room_total + svc_total
        )
    
    

    @staticmethod
    def find_closest_rooms(available_ids, quantity):
        available_ids.sort()
        
        n = len(available_ids)
        if n < quantity:
            return None 
        
        min_diff = float('inf')
        best_window = []
        
        for i in range(n - quantity + 1):
            current_window = available_ids[i : i + quantity]
            
            diff = current_window[-1] - current_window[0]
            
            if diff < min_diff:
                min_diff = diff
                best_window = current_window

            if diff == quantity - 1:
                break
                
        return best_window
    @staticmethod
    def suggest_service_combos(service_list, max_budget):
        """
        Sử dụng BACKTRACKING để tìm các tổ hợp dịch vụ
        có tổng giá <= max_budget.
        """
        results = []
        
        def backtrack(start_idx, current_combo, current_total):
            if current_total > 0:
                results.append({
                    "combo": list(current_combo), 
                    "total": current_total
                })
            
            for i in range(start_idx, len(service_list)):
                item = service_list[i]
                
                if current_total + item.price > max_budget:
                    continue
                
                current_combo.append(item.name)
                
                backtrack(i + 1, current_combo, current_total + item.price)
                
                current_combo.pop()

        service_list.sort(key=lambda x: x.price)
        backtrack(0, [], 0)
        
        results.sort(key=lambda x: x['total'], reverse=True)
        return results[:5]