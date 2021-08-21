from flask import Flask, request, abort
from flask_restplus import Api, Resource
from ph4_walkingpad import pad
from ph4_walkingpad.pad import WalkingPad, Controller
from ph4_walkingpad.utils import setup_logging
import asyncio
import yaml
import psycopg2
from datetime import date

flask_app = Flask(__name__)
app = Api(app=flask_app)
name_space = app.namespace('', description='WalkingPad API')

log = setup_logging()
pad.logger = log
ctler = Controller()

last_status = None


def on_new_status(sender, record):
    last_status = record

    distance_in_km = record.dist / 100
    print("Received Record:")
    print('Distance: {0}km'.format(distance_in_km))
    print('Time: {0} seconds'.format(record.time))
    print('Steps: {0}'.format(record.steps))

    print("Storing in DB...")
    store_in_db(record.steps, distance_in_km, record.time)


def store_in_db(steps, distance_in_km, duration_in_seconds):
    try:
        db_config = load_config()['database']
        conn = psycopg2.connect(host=db_config['host'], port=db_config['port'],
                                dbname=db_config['dbname'], user=db_config['user'], password=db_config['password'])
        cur = conn.cursor()

        date_today = date.today().strftime("%Y-%m-%d")
        duration = int(duration_in_seconds / 60)

        cur.execute("INSERT INTO exercise VALUES ('{0}', {1}, {2}, {3})".format(
            date_today, steps, duration, distance_in_km))
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


def save_config(config):
    with open('config.yaml', 'w') as outfile:
        yaml.dump(config, outfile, default_flow_style=False)


async def connect():
    address = load_config()['address']
    print("Connecting to {0}".format(address))
    await ctler.run(address)
    await asyncio.sleep(1.0)


async def disconnect():
    await ctler.disconnect()
    await asyncio.sleep(1.0)


@name_space.route("/config/address", methods=['GET', 'POST'])
class ConfigAddress(Resource):
    @name_space.doc(responses={200: "Currently set bluetooth address of WalkingPad"})
    def get(self):
        config = load_config()
        return str(config['address']), 200

    @name_space.doc(
        params={'address': "The bluetooth mac address of the walking pad"},
        responses={
            202: "Saves new address"
        })
    def post(self):
        address = request.args.get('address')
        config = load_config()
        config['address'] = address
        save_config(config)

        return self.get()


@name_space.route("/walkingpad/mode", methods=['POST'])
class WalkingPadMode(Resource):
    @name_space.doc(
        params={'mode': "Standby or Manual"},
        responses={
            200: "WalkingPad Mode changed",
            404: "Specified Mode not supported"
        })
    async def post(self):
        mode = request.args.get('mode')
        print("Got mode {0}".format(mode))

        pad_mode = None
        if (mode.lower() == "standby"):
            pad_mode = WalkingPad.MODE_STANDBY
        elif (mode.lower() == "manual"):
            pad_mode = WalkingPad.MODE_MANUAL
        else:
            return "Mode {0} is not supported".format(mode), 404

        try:
            await connect()

            await ctler.switch_mode(pad_mode)
            await asyncio.sleep(1.0)
        finally:
            await disconnect()

        return str(pad_mode), 200


@name_space.route("/walkingpad/history", methods=['GET'])
class WalkingPadDataCollector(Resource):
    @name_space.doc(
        responses={
            200: "Last WalkingPad History Record"
        }
    )
    async def get(self):
        try:
            await connect()
            
            await ctler.ask_hist(0)
            await asyncio.sleep(1.0)
        finally:
            await disconnect()
            
        return last_status, 200

ctler.handler_last_status = on_new_status

if __name__ == '__main__':
    flask_app.run(debug=True, host='0.0.0.0', port=5678)
