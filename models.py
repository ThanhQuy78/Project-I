from dataclasses import dataclass
from datetime import datetime

@dataclass
class Room:
    id: int
    status: str
    type_id: int
    type_name: str
    price: float
    capacity: int
    note : str = ""

@dataclass
class Service:
    id: int
    name: str
    price: float

@dataclass
class BillDetail:
    ma_hd: int
    ma_pd: int
    customer_name: str
    check_in: datetime
    check_out: datetime
    days_used: int
    room_price: float
    room_total: float
    service_items: list 
    service_total: float
    grand_total: float