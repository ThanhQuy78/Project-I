from datetime import datetime
import math

class HotelAlgorithms:
    
    @staticmethod
    def analyze_availability(all_rooms, conflict_ids):
        busy_set = set(conflict_ids)
        

        stats_map = {} 

        for room in all_rooms:
            if room['id'] not in busy_set and room['status'] != 'Bảo trì':
                tid = room['type_id']
                
                if tid not in stats_map:
                    stats_map[tid] = {
                        "id": tid, "name": room['type_name'], 
                        "price": room['price'], "cap": room['cap'],
                        "count": 0, "room_ids": []
                    }
                
                stats_map[tid]["count"] += 1
                stats_map[tid]["room_ids"].append(room['id'])
        
        return list(stats_map.values())


    @staticmethod
    def binary_search_room(sorted_arr, target_id):
        low = 0
        high = len(sorted_arr) - 1
        while low <= high:
            mid = (low + high) // 2
            if sorted_arr[mid]['id'] == target_id: return sorted_arr[mid]
            elif sorted_arr[mid]['id'] < target_id: low = mid + 1
            else: high = mid - 1
        return None
    

    @staticmethod
    def calculate_bill_details(bill_data):
        """
        Hàm thuần túy tính toán (Pure Function).
        Input: Dữ liệu thô từ DB.
        Output: Dictionary chi tiết tiền.
        """
        check_in = bill_data['check_in_time']
        check_out = datetime.now()
        duration = check_out - check_in
        
        total_seconds = duration.total_seconds()
        hours_used = math.ceil(total_seconds / 3600)
        
        if hours_used < 1: hours_used = 1
        
        room_total = hours_used * bill_data['price_per_hour']

        service_total = 0
        service_details = []
        for s in bill_data['services']:
            subtotal = s['qty'] * s['price']
            service_total += subtotal
            service_details.append({
                "name": s['name'], "qty": s['qty'], 
                "price": s['price'], "subtotal": subtotal
            })

        grand_total = room_total + service_total
        
        return {
            "customer": bill_data['customer_name'],
            "check_in": check_in,
            "check_out": check_out,
            "hours": hours_used,
            "room_price": bill_data['price_per_hour'],
            "room_total": room_total,
            "services": service_details,
            "service_total": service_total,
            "grand_total": grand_total
        }

    @staticmethod
    def merge_sort_by_price(arr):
        if len(arr) <= 1: return arr
        mid = len(arr) // 2
        left = HotelAlgorithms.merge_sort_by_price(arr[:mid])
        right = HotelAlgorithms.merge_sort_by_price(arr[mid:])
        return HotelAlgorithms._merge(left, right)

    @staticmethod
    def _merge(left, right):
        res = []
        i = j = 0
        while i < len(left) and j < len(right):
            if left[i]['price'] <= right[j]['price']: 
                res.append(left[i])
                i += 1
            else: 
                res.append(right[j])
                j += 1
        res.extend(left[i:])
        res.extend(right[j:])
        return res