#!/usr/bin/env python3
# coding: utf-8

interval = 1 # 動作間隔

from bluepy import btle
from sys import argv
import getpass
from time import sleep
from datetime import datetime

import dothat.lcd as lcd

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
now= datetime.now()
#d  = '{0:0>4d}/{1:0>2d}/{2:0>2d}({3})'.format(now.year, now.month, now.day, now.strftime('%a'))
d  = '{0:0>4d}/{1:0>2d}/{2:0>2d}'.format(now.year, now.month, now.day)
#t  = '{0:0>2d}:{1:0>2d}:{2:0>2d}'.format(now.hour, now.minute) #, now.second)
t  = '{0:0>2d}:{1:0>2d}'.format(now.hour, now.minute) #, now.second)

import requests

def line_message(text):
    url    = "https://notify-api.line.me/api/notify"
    token  = "Zaj0BRu04W1aofVIm2AIxGdhuwI5fUayF9ji8sCBpru"
    headers= {"Authorization":"Bearer "+token,
            "Content-Type":"application/x-www-form-urlencoded"}
    #message = 'message送信！'
    payload = {"message":text, 
            "stickerPackageId":2, 
            "stickerId":513}
    r = requests.post(url ,headers = headers ,params=payload)

count    =0
start_seq=0
cur_cnt  =0
while True:
    # BLE受信処理
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
        #print("\nDevice %s (%s), RSSI=%d dB" % (dev.addr, dev.addrType, dev.rssi))
        isRohmMedal = False
        sensors = dict()
        for (adtype, desc, val) in dev.getScanData():
            #print("  %s = %s" % (desc, val))
            if desc == 'Short Local Name' and val[0:18] == 'ROHMMedal2_0040_01': #Short Local Name = ROHMMedal2_0040_01.00
                isRohmMedal = True
                print(val)
            if isRohmMedal and desc == 'Manufacturer':

                # センサ値を辞書型変数sensorsへ代入
                sensors['ID'] = hex(payval(2,2))
                sensors['Temperature'] = -45 + 175 * payval(4,2) / 65536
                sensors['Humidity'] = 100 * payval(6,2) / 65536
                sensors['SEQ'] = payval(8)
                SEQ = sensors['SEQ']
                if SEQ == 1:
                    start_seq+= 1
                    zero_time = datetime.now()
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
                                         + sensors['Geomagnetic Z'] ** 2) ** 0.5
                sensors['Pressure'] = payval(22,3) / 2048
                sensors['Illuminance'] = payval(25,2) / 1.2
                sensors['Magnetic'] = hex(payval(27))
                magnetic = sensors['Magnetic']
                """if magnetic != '0x3':
                    count+=1
                    print(count)"""

                sensors['Steps'] = payval(28,2)
                step_cnt = sensors['Steps']
                if start_seq > 0:
                    if start_seq == 1:
                        start_time = zero_time
                    cur_time= datetime.now()
                    dur_time= cur_time - start_time
                    cur_cnt = step_cnt
                    cur_cal = round(cur_cnt/4)
                    if cur_cnt != 0 and cur_cnt%100 == 0:
                        text = str(cur_cnt)+" jump completed!"
                        print(text)
                        line_message(text)
                    #t  = '{0:0>2d}:{1:0>2d}:{2:0>2d}'.format(now.hour, now.minute, now.second)
                    time_text= cur_time.strftime('%H:%M:%S')
                    dur_text = "Time {} {}".format(dur_time.seconds, dur_time)
                    jump_text= "Jump "+str(cur_cnt)+" Cal "+str(cur_cal) #+" JPM "+str(round(cur_cnt/dur_time.seconds))
                    print(time_text)
                    print(dur_text)
                    print(jump_text) #'Count:',cur_cnt,', Duration:',duration,'-',round(duration.seconds))
                    lcd.clear()
                    lcd.set_cursor_position(0,0)
                    lcd.write(time_text)
                    lcd.set_cursor_position(0,1)
                    lcd.write(dur_text)
                    lcd.set_cursor_position(0,2)
                    lcd.write(jump_text)

                sensors['Battery Level'] = payval(30)
                sensors['RSSI'] = dev.rssi

                # 画面へ表示
                #print('    ID            =',sensors['ID'])
                print('    SEQ           =',sensors['SEQ'])
                """print('    Temperature   =',round(sensors['Temperature'],2),'℃')
                print('    Humidity      =',round(sensors['Humidity'],2),'%')
                print('    Pressure      =',round(sensors['Pressure'],3),'hPa')
                print('    Illuminance   =',round(sensors['Illuminance'],1),'lx')
                print('    Accelerometer =',round(sensors['Accelerometer'],3),'g (',\
                                            round(sensors['Accelerometer X'],3),\
                                            round(sensors['Accelerometer Y'],3),\
                                            round(sensors['Accelerometer Z'],3),'g)')
                print('    Geomagnetic   =',round(sensors['Geomagnetic'],1),'uT (',\
                                            round(sensors['Geomagnetic X'],1),\
                                            round(sensors['Geomagnetic Y'],1),\
                                            round(sensors['Geomagnetic Z'],1),'uT)')"""
                #print('    Magnetic      =',sensors['Magnetic'])
                print('    Steps         =',sensors['Steps'],'Cnt')

                #print('    Battery Level =',sensors['Battery Level'],'%')
                #print('    RSSI          =',sensors['RSSI'],'dB')

                '''
                for key, value in sorted(sensors.items(), key=lambda x:x[0]):
                    print('    ',key,'=',value)
                '''

