# -*- coding:utf-8 -*-

import os
import time
import logging
from requests import HTTPError
from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException
from requests.compat import json
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import LegacyApplicationClient
from oauthlib.oauth2 import TokenExpiredError
import urllib.parse

_LOGGER = logging.getLogger(__name__)

BASE_URL = 'https://e-mind-api.eu.cloudhub.io/api/'
TOKEN_URL = 'https://mind-oauth2-provider.eu.cloudhub.io/external/access_token'
REFRESH_URL = TOKEN_URL


class Vehicle(object):
    def __init__(self, vehicle_id, mind_api, local_time=False):
        self._mind_api = mind_api
        self.vehicleId = vehicle_id
        self._local_time = local_time
#        self._vehicle = self._mind_api.vehicle(self.vehicleId)

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self._repr_name)

    @property
    def _vehicle(self):
        return self._mind_api._vehicle(self.vehicleId)
        # self._vehicle.get('Id')

    @property
    def id(self):
        return self.vehicleId

    @property
    def license_plate(self):
        return self._vehicle.get('registrationNumber')

    @property
    def mileage(self):
        return self._vehicle.get('odometer')

    @property
    def fuellevel(self):
        return self._vehicle.get('fuelLevel')

    @property
    def mileage_left(self):
        return self._vehicle.get('rangeFuel')

    @property
    def lat(self):
        return self._vehicle.get('lat')

    @property
    def lon(self):
        return self._vehicle.get('lon')

    @property
    def _repr_name(self):
        return self.license_plate


class Driver(object):
    def __init__(self, driver_id, mind_api, local_time=False):
        self._mind_api = mind_api
        self.driverId = driver_id
        self._local_time = local_time

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self._repr_name)

    @property
    def _driver(self):
        return self._mind_api._driver(self.driverId)

    @property
    def id(self):
        return self.driverId

    @property
    def first_name(self):
        return self._driver.get('firstName')

    @property
    def sur_name(self):
        return self._driver.get('lastName')

    @property
    def _repr_name(self):
        return self.first_name + ' ' + self.sur_name


class Mind(object):
    def __init__(self, username, password, client_id='f531922867194c7197b8df82da18042e',
                 client_secret='eB7ecfF84ed94CBDA825AC6dee503Fca', cache_ttl=270,
                 user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 12_0 like Mac OS X) AppleWebKit/605.1.15 '
                            '(KHTML, like Gecko) Mobile/16A5366a',
                 token=None, token_cache_file=None,
                 local_time=False):
        self._client_id = client_id
        self._client_secret = client_secret
        self._username = username
        self._password = password
        self._token = token
        self._token_cache_file = token_cache_file
        self._cache_ttl = cache_ttl
        self._cache = {}
        self._local_time = local_time
        self._user_agent = user_agent

        self._auth()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def _token_saver(self, token):
        self._token = token
        if self._token_cache_file is not None:
                with os.fdopen(os.open(self._token_cache_file,
                                       os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600),
                               'w') as f:
                    json.dump(token, f)

    def _auth(self):
            self._mindApi = OAuth2Session(client=LegacyApplicationClient(client_id=self._client_id))
            token = self._mindApi.fetch_token(token_url=TOKEN_URL, username=self._username, password=self._password,
                                              auth=HTTPBasicAuth(self._client_id, self._client_secret))
            self._token_saver(token)

    def _reauth(self):
        if self._token_cache_file is not None and self._token is None and os.path.exists(self._token_cache_file):
                with open(self._token_cache_file, 'r') as f:
                    self._token = json.load(f)

        if self._token is not None:
            token = self._mindApi.refresh_token(REFRESH_URL, refresh_token=self._token.get("refresh_token"))
            self._token_saver(token)

    @property
    def cache_ttl(self):
        return self._cache_ttl

    @cache_ttl.setter
    def cache_ttl(self, value):
        self._cache_ttl = value

    def _get(self, endpoint, **params):
        query_string = urllib.parse.urlencode(params)
        url = BASE_URL + endpoint + '?' + query_string
        try:
            response = self._mindApi.get(url)
            response.raise_for_status()
            return response.json()
        except TokenExpiredError:
            _LOGGER.info("Token Expired")
            self._auth()
            return self._get(endpoint, **params)
        except HTTPError as e:
            _LOGGER.error("HTTP Error mind API: %s" % e)
        except RequestException as e:
            _LOGGER.error("Error mind API: %s" % e)

    def _post(self, endpoint, data, **params):
        query_string = urllib.parse.urlencode(params)
        url = BASE_URL + endpoint + '?' + query_string
        response = self._mindApi.post(url, json=data, client_id=self._client_id, client_secret=self._client_secret)
        response.raise_for_status()
        return response.status_code

    def _check_cache(self, cache_key):
        if cache_key in self._cache:
            cache = self._cache[cache_key]
        else:
            cache = (None, 0)

        return cache

    def _bust_cache_all(self):
        self._cache = {}

    def _bust_cache(self, cache_key):
        self._cache[cache_key] = (None, 0)

    @property
    def _vehicles(self):
        cache_key = 'vehicles'
        value, last_update = self._check_cache(cache_key)
        now = time.time()

        if not value or now - last_update > self._cache_ttl:
            new_value = self._get('vehicles')
            if new_value:
                value = new_value
                self._cache[cache_key] = (value, now)

        if value:
            return value.get('vehicleJsons')

    def _vehicle(self, vehicle_id):
        if self._vehicles:
            for vehicle in self._vehicles:
                if vehicle.get('vehicleId') == vehicle_id:
                    return vehicle

    @property
    def _drivers(self):
        cache_key = 'drivers'
        value, last_update = self._check_cache(cache_key)
        now = time.time()

        if not value or now - last_update > self._cache_ttl:
            new_value = self._get('drivers')
            if new_value:
                value = new_value
                self._cache[cache_key] = (value, now)
        if value:
            return value.get('drivers')

    def _driver(self, driver_id):
        if self._drivers:
            for driver in self._drivers:
                if driver.get('driverId') == driver_id:
                    return driver

    @property
    def drivers(self):
        return [Driver(driver.get('driverId'), self, self._local_time)
                for driver in self._drivers]

    @property
    def vehicles(self):
        return [Vehicle(vehicle.get('vehicleId'), self, self._local_time)
                for vehicle in self._vehicles]
