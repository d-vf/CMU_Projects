import requests
import time

def handle_request(url):
    retry_times = 5
    status_code = 0
    for count in range(retry_times):
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()["data"]
        status_code = response.status_code
        if status_code == 429:
            sleep_time = response.headers.get("Retry-after")
            time.sleep(int(sleep_time))
        else:
            time.sleep(6)

    raise Exception("request error, code = {}".format(status_code))