from time import time
from asyncio import sleep
from grpc import insecure_channel, RpcError, Call
from yagrc import reflector as yagrc_reflector
from pathlib import Path
from datetime import datetime
from telethon import TelegramClient

api_id = 'your_api_id'
api_hash = 'your_api_hash'
notifications_channel = 'some_channel'
dish_api_url = '192.168.100.1:9200'
timestamp_file = 'command_timestamp.txt'
log_file = 'starlink-gps-control.log'

client = TelegramClient('notificationbotua', api_id, api_hash)

async def main():
    reflector = yagrc_reflector.GrpcReflectionClient()
    
    while True:
        try:
            with insecure_channel(dish_api_url) as channel:
                reflector.load_protocols(channel, symbols=['SpaceX.API.Device.Device'])
                stub = reflector.service_stub_class('SpaceX.API.Device.Device')(channel)
                request_class = reflector.message_class('SpaceX.API.Device.Request')
                status_request = request_class(get_status={})
                response = stub.Handle(status_request, timeout=10)
                uptime_s = response.dish_get_status.device_state.uptime_s
                if uptime_s < 60:
                    file_path = Path(timestamp_file)
                    if file_path.is_file():
                        with open(timestamp_file, 'r') as file:
                            last_timestamp = float(file.read())
                    else:
                        last_timestamp = 0
                    time_delta = time() - last_timestamp
                    if time_delta < 60:
                        await sleep(10)
                        continue
                    else:
                        gps_request = request_class(dish_inhibit_gps={'inhibit_gps': True})
                        stub.Handle(gps_request, timeout=10)
                        metadata = await client.get_entity(notifications_channel)
                        await client.send_message(entity=metadata, message='ℹ️ Starlink has been rebooted')
                        with open(timestamp_file, 'w') as file:
                            file.write(str(time()))

        except RpcError as e:
            if isinstance(e, Call):
                with open(log_file, 'a') as file:
                    file.write(f'\n{datetime.now()} gRPC Communication Error: {e.details()}')
            else:
                with open(log_file, 'a') as file:
                    file.write(f'\n{datetime.now()} Unknown gRPC error occurred.')
        except Exception as e:
            with open(log_file, 'a') as file:
                file.write(f'\n{datetime.now()} Unexpected error: {e}')

        await sleep(10)

client.start()
client.loop.run_until_complete(main())