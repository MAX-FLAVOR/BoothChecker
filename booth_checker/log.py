from datetime import datetime

current_time = ''
def strftime_now():
    global current_time
    current_time = datetime.now().strftime('%Y-%m-%d %H %M')
    return current_time

def log_print(order_num, str):
    global current_time
    print(f'{current_time}: [{order_num}] {str}')
    
    