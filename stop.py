import asyncio
from ph4_walkingpad import pad
from ph4_walkingpad.pad import WalkingPad, Controller
from ph4_walkingpad.utils import setup_logging
import yaml
import psycopg2
from datetime import date

def on_new_status(sender, record):
    distance_in_km = record.dist / 100
    print("Received Record:")
    print('Distance: {0}km'.format(distance_in_km))
    print('Time: {0} seconds'.format(record.time))
    print('Steps: {0}'.format(record.steps))
    
    print("Storing in DB...")
    store_in_db(record.steps, distance_in_km, record.time)
    
    ctler.last_status = None
    
def store_in_db(steps, distance_in_km, duration_in_seconds):
    try:
        db_config = config['database']
        conn = psycopg2.connect(host=db_config['host'], port=db_config['port'], dbname=db_config['dbname'], user=db_config['user'], password=db_config['password'])
        cur = conn.cursor()
        
        date_today = date.today().strftime("%Y-%m-%d")
        duration = int(duration_in_seconds / 60)
        
        cur.execute("INSERT INTO exercise VALUES ('{0}', {1}, {2}, {3})".format(date_today, steps, duration, distance_in_km))
        conn.commit()
        
    finally:
        cur.close()
        conn.close()
    
def load_config():
    with open("config.yaml", 'r') as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    
config = load_config()

log = setup_logging()
pad.logger = log
ctler = Controller()
ctler.handler_last_status = on_new_status

async def connect():
    address = config['address']
    print("Connecting to {0}".format(address))
    await ctler.run(address)

async def disconnect():
    await ctler.disconnect()

async def set_to_standby():
    await ctler.switch_mode(WalkingPad.MODE_STANDBY)

async def get_stats():
    await ctler.ask_hist(0)
    await asyncio.sleep(1.0)
    
async def main():
    try:
        print("Connecting...")
        await connect()
        await asyncio.sleep(1.0)
        
        print("Getting Setting to standby...")
        await set_to_standby()
        await asyncio.sleep(1.0)
        
        print("Getting Stats...")
        await get_stats()
        await asyncio.sleep(1.0)
    
    finally:
        print("Disconnecting from device")
        await disconnect()
        await asyncio.sleep(1.0)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()