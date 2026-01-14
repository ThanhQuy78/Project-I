class Config:
    SERVER = '.\\SQLEXPRESS'           
    DATABASE = 'HotelManagementDB'
    DRIVER = '{ODBC Driver 17 for SQL Server}'
    CONNECTION_STRING = f'DRIVER={DRIVER};SERVER={SERVER};DATABASE={DATABASE};Trusted_Connection=yes;'
    MASTER_CONN_STR = f'DRIVER={DRIVER};SERVER={SERVER};Trusted_Connection=yes;AutoCommit=True;'