#!/usr/bin/env python3
# coding: utf-8

from tkinter import *
from datetime import datetime

# メインウィンドウ作成
root = Tk()

# メインウィンドウサイズ
root.geometry("1024x600") #720x480")

# メインウィンドウタイトル
root.title("Jump")

# Canvas 作成
c = Canvas(root, bg="#FFFFFF", width=1024, height=600) #720, height=480)
c.pack(expand=True, fill=BOTH)

# 文字列作成
ch = c.create_text(520, 30, font=('', 30, ''), fill='black')
c1 = c.create_text(500, 80, font=('', 30, ''), fill='black')
c2 = c.create_text(500, 150, font=('', 55, 'bold'), fill='red')
c3 = c.create_text(500, 250, font=('', 45, ''), fill='blue')
c4 = c.create_text(500, 350, font=('', 30, ''), fill='green')
c5 = c.create_text(500, 420, font=('', 30, ''), fill='green')

# 画面がリサイズされたとき
def change_size(event):
    # 画面の中心座標を取得
    w = c.winfo_width()  / 2
    h = c.winfo_height() / 2

    # 文字列の矩形の中心座標を取得
    cd_coords = c.bbox(cd)
    cd_w = cd_coords[0] + (cd_coords[2] - cd_coords[0]) / 2
    cd_h = cd_coords[1] + (cd_coords[3] - cd_coords[1]) / 2
    ct_coords = c.bbox(ct)
    ct_w = ct_coords[0] + (ct_coords[2] - ct_coords[0]) / 2
    ct_h = ct_coords[1] + (ct_coords[3] - ct_coords[1]) / 2

    # 中心座標を合わせるように移動
    c.move(cd, w - cd_w, h - cd_h - 60)
    c.move(ct, w - ct_w, h - ct_h + 60)

interval = 1 # 動作間隔

from bluepy import btle
from sys import argv
import getpass
from time import sleep
from datetime import datetime
json_dir = "/home/pi/Programs/"
import json
json_open = open(json_dir+'tokai53.json', 'r')
json_load = json.load(json_open)

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
d  = '{0:0>4d}/{1:0>2d}/{2:0>2d}'.format(now.year, now.month, now.day)
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


from spreadsheet import SpreadSheet
spreadsheet_name  = '1a_PQovhySYPV5D-rGhs1Soh7pvhGWmVltSPsSX_VmuA'
key_name = json_dir+'raspberryai-62aca965a8af.json'
sheet_name= 'raspi-jump-drive' #Sheet1' # シート名

sheet = SpreadSheet(spreadsheet_name) #'1a_PQovhySYPV5D-rGhs1Soh7pvhGWmVltSPsSX_VmuA')

import gspread
from oauth2client.service_account import ServiceAccountCredentials

def get_spreadsheet(searchKey):
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(key_name, scope)
    gc = gspread.authorize(credentials)     # JSONキーファイルで認証
    wks = gc.open(sheet_name).sheet1        # sheetをオープン
    records = wks.get_all_values()          # 中身を取り出して配列に保存
    for i in range(1, len(records)):        # sheetの行数分だけ繰り返す
        if records[i][0] == searchKey:     # １列目がTerminalIDと一致するま>で
            gdate=records[i][0]
            gtime=records[i][1]
            gjump=records[i][2]
            gdur =records[i][3]
            gcal =records[i][4]
            gdist=records[i][5]
            print(gdate, gtime, gjump, gdur, gcal, gdist)
    return gdate, gtime, gjump, gdur, gcal, gdist

# 画面のリサイズをバインドする
root.bind('<Configure>', change_size)

# メインウィンドウの最大化
root.attributes("-zoomed", "1")

# 常に最前面に表示
root.attributes("-topmost", True)

"""def cupdate():
    # 現在時刻を表示
    now = datetime.now()
    d = '{0:0>4d}/{1:0>2d}/{2:0>2d} ({3}.)'.format(now.year, now.month, now.day, now.strftime('%a'))
    t = '{0:0>2d}:{1:0>2d}:{2:0>2d}'.format(now.hour, now.minute, now.second)
"""

start_seq = 0
start_text= 'ボタンを押して、ジャンプスタート！'
start_time= datetime.now()
last_cnt  = 0
last_time = datetime.now()
last_dur  = 0
last_cal  = 0
last_mv   = 0

while True:

    c.itemconfigure(ch, text=start_text)

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
            if isRohmMedal and desc == 'Manufacturer':

                # センサ値を辞書型変数sensorsへ代入
                sensors['ID'] = hex(payval(2,2))
                sensors['Temperature'] = -45 + 175 * payval(4,2) / 65536
                sensors['Humidity'] = 100 * payval(6,2) / 65536
                sensors['SEQ'] = payval(8)
                SEQ = sensors['SEQ']
                """if SEQ in [255, 0, 1]:
                    start_seq+= 1
                    zero_time = datetime.now()"""

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

                sensors['Steps'] = payval(28,2)
                step_cnt = sensors['Steps']
                if SEQ in [255,0,1] and step_cnt == 0:
                    start_seq+= 1
                    start_time= datetime.now()
                    start_text= str(start_seq)+"回目を"+start_time.strftime('%H:%M:%S')+"にスタート。前回は"+last_time.strftime('%H:%M:%S')+"に"+str(last_cnt)
                    if last_cnt!=0:
                        line_message(start_text)
                        sheet.append([last_time.strftime('%Y/%m/%d'), last_time.strftime('%H:%M:%S'), 
                            last_cnt, last_dur, last_cal, last_mv])
                else:
                    last_time= start_time
                    last_cnt = step_cnt

                cur_time= datetime.now()
                time_text= cur_time.strftime('%Y/%m/%d(%a) %H:%M:%S')
                print(time_text)
                c.itemconfigure(c1, text=time_text)

                if start_seq >= 1:
                    dur_time= cur_time - start_time
                    cur_cnt = round(step_cnt*1.5)
                    cur_cal = round(cur_cnt/4)
                    cur_mv  = round(cur_cnt/1000,1)

                    #t  = '{0:0>2d}:{1:0>2d}:{2:0>2d}'.format(now.hour, now.minute, now.second)
                    dur_seconds = dur_time.seconds 
                    if dur_seconds > 3600:
                        dur_text = str(round(dur_seconds / 3600,1)) + "時間"
                    elif dur_seconds > 60:
                        dur_text = str(round(dur_seconds / 60)) + "分"
                    else:
                        dur_text = str(dur_seconds) + "秒"
                    jump_text= dur_text+"！"+str(cur_cnt)+"回！"+str(cur_cal)+"カロリ-！"
                    print(jump_text) #'Count:',cur_cnt,', Duration:',duration,'-',round(duration.seconds))

                    c.itemconfigure(ch, text="{}回目のチャレンジ！目指せ1日1000回!".format(start_seq))
                    c.itemconfigure(c2, text=jump_text)
                    if cur_cnt > 10:
                        comp_text = str(cur_cnt)+"回跳んだよ！"
                        if cur_cnt%100 == 0:
                            line_message(comp_text)
                        elif cur_cnt%10 == 0:
                            totals = get_spreadsheet('Total')
                            total_jump= totals[2]
                            total_dur = totals[3]
                            total_hour= round(int(total_dur)/3600,1)
                            total_cal = totals[4]
                            total_food= round(float(total_cal)/200)
                            total_mv  = totals[5]
                            stations  = json_load['stations']
                            for v in stations:
                                dist     = v['dist']
                                acc_dist = v['acc_dist']
                                prev_dist= acc_dist-dist
                                if prev_dist < int(total_mv) < acc_dist:
                                  cur_num = v['num']
                                  cur_name= v['name']
                                  cur_dist= dist
                                  cur_acc_dist= acc_dist
                                  #next_name = v[cur_num+1]['name']
                            mv_text   = str(cur_mv)+"Km進んだよ("+cur_name+"宿まで後"+str(round(cur_acc_dist-int(total_mv)))+"Km)"
                            c.itemconfigure(c3, text=mv_text)
                            total_text = "トータル"+str(total_hour)+"時間"+total_jump+"回跳んで"+total_cal+"カロリ-消費!"
                            goal_text  = "おにぎり"+str(total_food)+"個分、江戸から"+total_mv+"Km!(残り"+str(round(550-int(total_mv)))+"Km)"
                            c.itemconfigure(c4, text=total_text)
                            c.itemconfigure(c5, text=goal_text)

                    last_dur = dur_seconds
                    last_cal = cur_cal
                    last_mv  = cur_mv

                    """lcd.clear()
                    lcd.set_cursor_position(0,0)
                    lcd.write(time_text)
                    lcd.set_cursor_position(0,1)
                    lcd.write(dur_text)
                    lcd.set_cursor_position(0,2)
                    lcd.write(jump_text)"""

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

    #c.itemconfigure(ch, text='Jump!')
    #c.itemconfigure(cd, text=d)
    #c.itemconfigure(ct, text=t)
                c.update()

    # 1秒間隔で繰り返す
    #root.after(1000, cupdate)

# コールバック関数を登録
#root.after(1000, cupdate)

# メインループ
root.mainloop()

