#!/usr/bin/env python3
# coding: utf-8

from __future__ import (division, absolute_import, print_function,
                                unicode_literals)

import fcntl
import socket
import struct

import dothat
import dothat.backlight as backlight
import dothat.lcd as lcd

def get_addr(ifname):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(
            fcntl.ioctl(
                s.fileno(),
                0x8915,  # SIOCGIFADDR
                struct.pack('256s', ifname[:15].encode('utf-8')))[20:24])
    except IOError:
        return 'Not Found!'


eth0 = get_addr('eth0')
host = socket.gethostname()

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
    wlan0 = get_addr('wlan0')

    lcd.clear()
    lcd.set_cursor_position(0, 0)
    lcd.write('{}'.format(wlan0))
    lcd.set_cursor_position(0, 1)
    lcd.write('{}'.format(d))
    lcd.set_cursor_position(2, 2)
    lcd.write('{}'.format(t))

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
            if desc == 'Short Local Name' and val[0:18] == 'ROHMMedal2_0107_01': #val[0:10] == 'ROHMMedal2':
                isRohmMedal = True
            if isRohmMedal and desc == 'Manufacturer':

                # センサ値を辞書型変数sensorsへ代入
                sensors['ID'] = hex(payval(2,2))
                sensors['Temperature'] = -45 + 175 * payval(4,2) / 65536
                sensors['Humidity'] = 100 * payval(6,2) / 65536
                """sensors['SEQ'] = payval(8)
                sensors['Condition Flags'] = bin(int(val[16:18],16))
                sensors['Accelerometer X'] = payval(10,2,True) / 4096
                sensors['Accelerometer Y'] = payval(12,2,True) / 4096
                sensors['Accelerometer Z'] = payval(14,2,True) / 4096
                sensors['Accelerometer'] = (sensors['Accelerometer X'] ** 2\
                                          + sensors['Accelerometer Y'] ** 2\
                                          + sensors['Accelerometer Z'] ** 2) ** 0.5
                sensors['Geomagnetic X'] = payval(16,2,True) / 10
                sensors['Geomagnetic Y'] = payval(18,2,True) / 10
                sensors['Geomagnetic Z'] = payval(20,2,True) / 10
                sensors['Geomagnetic']  = (sensors['Geomagnetic X'] ** 2\
                                         + sensors['Geomagnetic Y'] ** 2\
                                         + sensors['Geomagnetic Z'] ** 2) ** 0.5"""
                sensors['Pressure'] = payval(22,3) / 2048
                sensors['Illuminance'] = payval(25,2) / 1.2
                """sensors['Magnetic'] = hex(payval(27))
                sensors['Steps'] = payval(28,2)"""
                sensors['Battery Level'] = payval(30)
                sensors['RSSI'] = dev.rssi

                # 画面へ表示
                print('    ID            =',sensors['ID'])
                #print('    SEQ           =',sensors['SEQ'])
                print('    Temperature   =',round(sensors['Temperature'],2),'℃')
                print('    Humidity      =',round(sensors['Humidity'],2),'%')
                print('    Pressure      =',round(sensors['Pressure'],3),'hPa')
                print('    Illuminance   =',round(sensors['Illuminance'],1),'lx')
                """print('    Accelerometer =',round(sensors['Accelerometer'],3),'g (',\
                                            round(sensors['Accelerometer X'],3),\
                                            round(sensors['Accelerometer Y'],3),\
                                            round(sensors['Accelerometer Z'],3),'g)')
                print('    Geomagnetic   =',round(sensors['Geomagnetic'],1),'uT (',\
                                            round(sensors['Geomagnetic X'],1),\
                                            round(sensors['Geomagnetic Y'],1),\
                                            round(sensors['Geomagnetic Z'],1),'uT)')
                print('    Magnetic      =',sensors['Magnetic'])
                print('    Steps         =',sensors['Steps'],'歩')"""
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
                    #dothat.backlight.single_rgb(1, 255, 0, 0)
                    backlight.rgb(255, 0, 0)
                else:
                    temp_msg = "Comfort"
                illum = sensors['Illuminance']
                if illum < 300:
                    illum_msg = "Dark!"
                    os.system("sudo hub-ctrl -b 1 -d 2 -P 2 -p 1")
                    #dothat.backlight.single_rgb(2, 255, 255, 255)
                    backlight.rgb(255, 255, 255)
                else:
                    illum_msg = "Bright"
                    os.system("sudo hub-ctrl -b 1 -d 2 -P 2 -p 0")
                    #dothat.backlight.single_rgb(2, 0, 0, 255)
                    backlight.rgb(0, 0, 255)

                human_msg = str(human_count)
                dothat.backlight.off()
                for led in range(human_count):
                    backlight.graph_set_led_state(led, 0.2)
                if human_count > human_check:
                    human_msg += ' Take Rest!'
                    lcd.clear()
                    #dothat.backlight.single_rgb(3, 0, 255, 0)
                    backlight.rgb(0, 255, 0)
                else:
                    human_msg += ' Work Hard!'
                    lcd.clear()
                    #dothat.backlight.single_rgb(3, 0, 255, 255)
                    backlight.rgb(0, 255, 255)

                lcd.clear()
                lcd.set_cursor_position(0, 0)
                lcd.write('T:{0:1.0f}C {1:1.0f}% {2}'.format(temp,humid,temp_msg))
                lcd.set_cursor_position(0, 1)
                lcd.write('I:{0:1.0f} Lx {1}'.format(illum,illum_msg))
                lcd.set_cursor_position(0, 2)
                lcd.write('H:{}'.format(human_msg))
                sleep(interval)

