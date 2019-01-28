
import json
import os
import requests
import time
import calendar, datetime

try:
    from urllib.parse import quote
except:
    from urllib import quote

from asset.icon import RAIN, STORM, SUN
from renderer.renderer import Anchor

CACHE_FILEPATH = os.path.expanduser('~/weather_{}.data')
SHOULD_REFRESH_SECONDS = 60 * 60


def current_utc_timestamp():
    utc_now = datetime.datetime.utcnow()
    return calendar.timegm(utc_now.timetuple())


def should_refresh(last_timestamp):
    current_timestamp = current_utc_timestamp()
    return current_timestamp > last_timestamp + SHOULD_REFRESH_SECONDS


def fetch_current_weather(woeid):
    url = 'https://www.metaweather.com/api/location/{}'.format(woeid)
    response = json.loads(requests.get(url).text)

    data = {
        'timestamp': current_utc_timestamp(),
        'data': response,
    }

    with open(CACHE_FILEPATH.format(woeid), 'w') as file:
        file.write(json.dumps(data))

    return response


def read_cached_weather(woeid):
    try:
        with open(CACHE_FILEPATH.format(woeid), 'r') as file:
            contents = json.loads(file.read())
            return (contents['timestamp'], contents['data'])
    except Exception:
        return (None, None)


def get_current_weather(woeid):
    timestamp, data = read_cached_weather(woeid)

    if not timestamp or should_refresh(timestamp):
        print('Refreshing weather data for:', woeid)
        data = fetch_current_weather(woeid)

        weather = data['consolidated_weather'][0]
        print(weather['the_temp'], weather['min_temp'], weather['max_temp'])

    return data


def current_temperature(data):
    def to_fehenheit(temp):
        return (temp * 9 / 5) + 32

    today_weather = data['consolidated_weather'][0]
    return to_fehenheit(today_weather['the_temp'])


class WeatherPlugin:
    def __init__(self):
        self._renderer = None
        self._weather = None

    def setup_plugin(self, instance, renderer):
        print('Setting up WeatherPlugin...')

        self._renderer = renderer
        self._weather = get_current_weather(2455920)
        self.update()

    def update(self):
        if self._weather:
            current_temp = current_temperature(self._weather)
            current_temp_str = '{0:.0f}'.format(current_temp)

            self._renderer.draw_string(current_temp_str,
                                       anchor=Anchor.BOTTOM | Anchor.RIGHT,
                                       icon=(STORM, Anchor.RIGHT))

