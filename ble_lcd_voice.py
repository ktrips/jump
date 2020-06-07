#!/usr/bin/env python3
# coding: utf-8

import dothat
import dothat.backlight as backlight
import dothat.lcd as lcd

interval = 10 # 動作間隔

from datetime import datetime
from bluepy import btle
from sys import argv
import getpass
from time import sleep

import os
import RPi.GPIO as GPIO
human_pin = 13
GPIO.setmode(GPIO.BCM)
GPIO.setup(human_pin, GPIO.IN)
human_count = 0
human_check = 3

import json
import requests
import sys

from pytz import timezone

API_KEY = "xxx" #WeatherMap API Key
ZIP = "123-4567,JP" #Your address
API_URL = "http://api.openweathermap.org/data/2.5/forecast?zip={0}&units=metric&lang=ja&APPID={1}"
aquest_path = "/home/pi/Programs/aquestalkpi/" #AquesTalkPi path

def getWeatherForecast():
    url = API_URL.format(ZIP, API_KEY)
    response = requests.get(url)
    forecastData = json.loads(response.text)
    if not ('list' in forecastData):
            print('error')
            return                        
    #print(forecastData)
    for item in forecastData['list']:
        forecastDatetime = timezone('Asia/Tokyo').localize(datetime.fromtimestamp(item['dt']))
        weatherDescription = item['weather'][0]['description']
        temperature = item['main']['temp']
        rainfall = 0
        if 'rain' in item and '3h' in item['rain']:
            rainfall = item['rain']['3h']
        break

    print('Date:{0} Weather:{1} Temp:{2} C Rain:{3}mm'.format(forecastDatetime, weatherDescription, temperature, rainfall))
    return forecastDatetime, weatherDescription, temperature, rainfall

def payval(num, bytes=1, sign=False):
    global val
    a = 0
    for i in range(0, bytes):
        a += (256 ** i) * int(val[(num - 2 + i) * 2 : (num - 1 + i) * 2],16)
    if sign:
        if a >= 2 ** (bytes * 8 - 1):
            a -= 2 ** (bytes * 8)
    return a

scanner = btle.Scanner()
while True:
    now = datetime.now()
    d = '{0:0>4d}/{1:0>2d}/{2:0>2d}({3})'.format(now.year, now.month, now.day, now.strftime('%a'))
    t = '{0:0>2d}:{1:0>2d}:{2:0>2d}'.format(now.hour, now.minute, now.second)
    forecastDatetime, weatherDescription, temperature, rainfall = getWeatherForecast()

    lcd.clear()
    lcd.set_cursor_position(0, 0)
    lcd.write('{}'.format(d))
    lcd.set_cursor_position(2, 1)
    lcd.write('{}'.format(t))
    lcd.set_cursor_position(0, 2)
    lcd.write('W:{1}C {2}mm'.format(round(temperature,0), rainfall))
    if rainfall > 0:
          print(weatherDescription, rainfall)
          os.system(aquest_path+'AquesTalkPi '+weatherDescription+' | aplay')
          
    human = GPIO.input(human_pin)
    if human == 1:
      human_count+=1
    else:
      human_count=0
    print('HCount:'+str(human_count))

    try:
        devices = scanner.scan(interval)
    except Exception as e:
        print("ERROR",e)
        if getpass.getuser() != 'root':
            print('使用方法: sudo', argv[0])
            exit()
        sleep(interval)
        continue

    # 受信データについてBLEデバイス毎の処理
    for dev in devices:
        print("\nDevice %s (%s), RSSI=%d dB" % (dev.addr, dev.addrType, dev.rssi))
        isRohmMedal = False
        sensors = dict()
        for (adtype, desc, val) in dev.getScanData():
            print("  %s = %s" % (desc, val))
            if desc == 'Short Local Name' and val[0:10] == 'ROHMMedal2':
                isRohmMedal = True
            if isRohmMedal and desc == 'Manufacturer':
                # センサ値を辞書型変数sensorsへ代入
                sensors['ID'] = hex(payval(2,2))
                sensors['Temperature'] = -45 + 175 * payval(4,2) / 65536
                sensors['Humidity'] = 100 * payval(6,2) / 65536
                sensors['Pressure'] = payval(22,3) / 2048
                sensors['Illuminance'] = payval(25,2) / 1.2
                sensors['Battery Level'] = payval(30)
                sensors['RSSI'] = dev.rssi

                # 画面へ表示
                print('    ID            =',sensors['ID'])
                print('    Temperature   =',round(sensors['Temperature'],2),'℃')
                print('    Humidity      =',round(sensors['Humidity'],2),'%')
                print('    Pressure      =',round(sensors['Pressure'],3),'hPa')
                print('    Illuminance   =',round(sensors['Illuminance'],1),'lx')
                print('    Battery Level =',sensors['Battery Level'],'%')
                print('    RSSI          =',sensors['RSSI'],'dB')

                '''
                for key, value in sorted(sensors.items(), key=lambda x:x[0]):
                    print('    ',key,'=',value)
                '''

                temp  = sensors['Temperature']
                humid = sensors['Humidity']
                lcd.clear()
                dothat.backlight.set_graph(0.5) # 50%
                backlight.rgb(0, 0, 0)
                if temp > 28 or humid > 80:
                    temp_msg = "Hot!"
                    backlight.rgb(255, 0, 0) #Red
                else:
                    temp_msg = "Not bad"
          
                illum = sensors['Illuminance']
                if illum < 200:
                    illum_msg = "Dark!"
                    os.system("sudo hub-ctrl -b 1 -d 2 -P 2 -p 1")
                    backlight.rgb(255, 255, 255)
                else:
                    illum_msg = "Bright"
                    os.system("sudo hub-ctrl -b 1 -d 2 -P 2 -p 0")
                    backlight.rgb(0, 0, 255) #Blue

                human_msg = str(human_count)
                dothat.backlight.off()
                for led in range(human_count):
                    backlight.graph_set_led_state(led, 0.2)
                if human_count > human_check:
                    human_msg += ' Take Rest!'
                    backlight.rgb(0, 255, 0) #Green
                    os.system(aquest_path+'AquesTalkPi "休憩しましょう！" | aplay')
                else:
                    human_msg += ' Work Hard!'
                    backlight.rgb(0, 255, 255) #Lightblue

                lcd.clear()
                lcd.set_cursor_position(0, 0)
                lcd.write('T:{0:1.0f}C {1:1.0f}% {2}'.format(temp,humid,temp_msg))
                lcd.set_cursor_position(0, 1)
                lcd.write('I:{0:1.0f} Lx {1}'.format(illum,illum_msg))
                lcd.set_cursor_position(0, 2)
                lcd.write('H:{}'.format(human_msg))
          
                sleep(interval)
