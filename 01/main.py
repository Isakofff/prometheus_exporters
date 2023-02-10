import requests
import subprocess
import time
from google.protobuf.timestamp_pb2 import Timestamp
from prometheus_client import start_http_server, Gauge

BLOCK_NUMBER = Gauge("block_number", "Number of the current block")
OUT_OF_SYNC = Gauge("out_of_sync", "Out of sync in seconds")
PEER_COUNT = Gauge("peer_count", "Number of peers")


def parse_status_page():
    url = "http://localhost:26657/status"
    response = requests.get(url)
    data = response.json()
    latest_block_height = data["result"]["sync_info"]["latest_block_height"].strip()
    latest_block_time = data["result"]["sync_info"]["latest_block_time"].strip()
    # print(latest_block_height)
    # print(latest_block_time)
    return latest_block_height, latest_block_time


def get_peer_count():
    # # localhost:26660/api/v1/query - this feature (tendermint api?) doesn't work as Prometheus API
    # import requests
    # URL = 'http://localhost:26660/api/v1/query'
    # PROMQL = {'query': 'tendermint_p2p_peers'}
    # response = requests.get(url = URL, params = PROMQL)
    # results = response.json()

    cmd = "curl -s localhost:26660/metrics | egrep '^tendermint_p2p_peers' | awk '{print $2}'"
    result = subprocess.check_output(cmd, shell=True)
    return result.decode().strip()


def count_out_of_sync(lbt):
    current_timestamp = Timestamp()
    current_timestamp.GetCurrentTime()

    block_timestamp = Timestamp()
    block_timestamp.FromJsonString(lbt)

    difference = current_timestamp.seconds - block_timestamp.seconds

    return difference


def get_metrics():
    latest_block_height, latest_block_time = parse_status_page()
    out_of_sync = count_out_of_sync(latest_block_time)

    BLOCK_NUMBER.set(int(latest_block_height))
    OUT_OF_SYNC.set(out_of_sync)
    PEER_COUNT.set(get_peer_count())

    # print(latest_block_height)
    # print(out_of_sync)
    # print(get_peer_count())


if __name__ == "__main__":
    # get_metrics()

    # Start up the server to expose the metrics
    start_http_server(8000)
    while True:
        get_metrics()
        time.sleep(1)
