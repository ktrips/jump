#! /usr/bin/python3
# -*- coding: utf-8 -*-
import json
import datetime
import os
import requests
import sys

from pytz import timezone

API_KEY = "05369ea6b08123aeacb3f72bb7f24ac2"
ZIP = "157-0066,JP"
API_URL = "http://api.openweathermap.org/data/2.5/forecast?zip={0}&units=metric&lang=ja&APPID={1}"

def getWeatherForecast():
    url = API_URL.format(ZIP, API_KEY)
    response = requests.get(url)
    forecastData = json.loads(response.text)

    if not ('list' in forecastData):
            print('error')
            return
                                        
    #print(forecastData)
    for item in forecastData['list']:
        forecastDatetime = timezone(
                                            'Asia/Tokyo').localize(datetime.datetime.fromtimestamp(item['dt']))
        weatherDescription = item['weather'][0]['description']
        temperature = item['main']['temp']
        rainfall = 0
        if 'rain' in item and '3h' in item['rain']:
            rainfall = item['rain']['3h']
        break

    print('Date:{0} Weather:{1} Temp:{2} C Rain:{3}mm'.format(
                                                                                                                                forecastDatetime, weatherDescription, temperature, rainfall))

getWeatherForecast()
