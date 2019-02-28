import base64
import calendar
import datetime
import hmac
import hashlib
import json
import time
import uuid

import urllib.parse
import urllib.request

API_URL = 'https://weather-ydn-yql.media.yahoo.com/forecastrss'
CLIENT_SECRET_PATH = 'yahoo_client_secret.json'

CACHE_FILEPATH = ('/tmp/weather_{}.data')
SHOULD_REFRESH_SECONDS = 60 * 60

class WeatherFetcher:
  def __init__(self):
    self._load_client_secret()

  def fetch(self, zipcode):
    query_params = self._generate_query_params(zipcode)
    oauth_header = self._generate_oauth_header(query_params)

    url = API_URL + '?' +urllib.parse.urlencode(query_params)
    request = urllib.request.Request(url)
    request.add_header('Authorization', oauth_header)
    request.add_header('Yahoo-App-Id', self._client_secret['app_id'])
    return json.loads(urllib.request.urlopen(request).read())

  def _load_client_secret(self):
    with open(CLIENT_SECRET_PATH, 'r') as file:
      self._client_secret = json.loads(file.read())

  def _generate_query_params(self, zipcode):
    return {
        'location': zipcode,
        'format': 'json'
    }

  def _generate_oauth_header(self, query_params):
    oauth_params = {
        'oauth_consumer_key': self._client_secret['key'],
        'oauth_nonce': uuid.uuid4().hex,
        'oauth_signature_method': 'HMAC-SHA1',
        'oauth_timestamp': str(int(time.time())),
        'oauth_version': '1.0',
    }

    client_secret = self._client_secret['secret']
    client_secret = '{}&'.format(client_secret).encode('UTF-8')

    merged_params = oauth_params.copy()
    merged_params.update(query_params)

    sorted_param_str = urllib.parse.urlencode(
        [(key, merged_params[key]) for key in sorted(merged_params)])

    signature_base =  '&'.join(('GET',
       urllib.parse.quote(API_URL, safe=''),
       urllib.parse.quote(sorted_param_str, safe=''))).encode('UTF-8')

    oauth_signature = hmac.new(
        client_secret, signature_base, hashlib.sha1).digest()
    oauth_signature = base64.b64encode(oauth_signature).decode('UTF-8')

    oauth_params['oauth_signature'] = oauth_signature
    return 'OAuth ' + ', '.join(
        ('{}="{}"'.format(k, v) for k, v in oauth_params.items()))


class CachedWeatherFetcher:
  def __init__(self):
    self._wrapped_fetched = WeatherFetcher()

  def fetch(self, zipcode):
    timestamp, data = self._read_cached_weather(zipcode)

    if not timestamp or self._should_refresh(timestamp):
      print('Refreshing weather data for:', zipcode)
      data = self._wrapped_fetched.fetch(zipcode)

      with open(CACHE_FILEPATH.format(zipcode), 'w') as file:
        file.write(json.dumps({
          'timestamp': self._current_utc_timestamp(),
          'data': data,
        }))

    return data

  def _current_utc_timestamp(self):
    utc_now = datetime.datetime.utcnow()
    return calendar.timegm(utc_now.timetuple())

  def _should_refresh(self, last_timestamp):
    current_timestamp = self._current_utc_timestamp()
    return current_timestamp > last_timestamp + SHOULD_REFRESH_SECONDS

  def _read_cached_weather(self, zipcode):
    try:
      with open(CACHE_FILEPATH.format(zipcode), 'r') as file:
        contents = json.loads(file.read())
        return (contents['timestamp'], contents['data'])
    except Exception:
      # Treat FileNotFound and corrupted data as no previous fetch.
      return (None, None)


fetcher = CachedWeatherFetcher()
output = json.dumps(fetcher.fetch('94040'), indent=2)
print(output)
