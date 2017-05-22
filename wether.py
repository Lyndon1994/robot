# -*- coding: utf-8 -*-
import requests, re

import db
import email_api

DEFAULT_CITY = '长安'

WETHER_FORECAST = 1
BAD_WETHER_REMIND = 2


# 天气预报
def today_wether(city=DEFAULT_CITY):
    w = requests.get('http://wthrcdn.etouch.cn/weather_mini?city=%s' % city)
    result = w.json()
    if result['status'] == 1000:
        data = result['data']
        today = data['forecast'][0]
        return '今天%s啦\n当前温度：%s℃\n今天是个%s天哦～最%s，最%s，%s %s\n%s' % (
            today['date'], data['wendu'], today['type'], today['high'], today['low'],
            today['fengxiang'], today['fengli'], data['ganmao'])


# 雨天提醒
def get_wether_remind(city=DEFAULT_CITY):
    w = requests.get('http://wthrcdn.etouch.cn/weather_mini?city=%s' % city)
    result = w.json()
    if result['status'] == 1000:
        data = result['data']
        today = data['forecast'][0]
        high = int(re.sub('\D', '', today['high']))
        low = int(re.sub('\D', '', today['low']))
        yesterday = data['yesterday']
        yesterday_high = int(re.sub('\D', '', yesterday['high']))
        yesterday_low = int(re.sub('\D', '', yesterday['low']))
        wencha = yesterday_high - high
        if '雨' in today['type']:
            return '今天是个%s天，记得带伞～' % today['type']
        elif '晴' in today['type'] and high > 34:
            return '今天太阳会很大啊，%s，注意防晒哦！' % today['high']
        elif wencha > 4:
            return '今天温度比昨天下降了%s℃，注意保暖！' % wencha
        else:
            return


def get_users(type):
    db.cursor.execute('SELECT username,email FROM users u JOIN wether_rss w ON u.id=w.user_id WHERE w.type=?', (type,))
    values = db.cursor.fetchall()
    return values


# 天气预报
def wether_forecast():
    users = get_users(type=WETHER_FORECAST)
    for user in users:
        email_api.send_email(user=user, header='天气预报', text=today_wether())


# 坏天气预报
def wether_remind():
    users = get_users(type=BAD_WETHER_REMIND)
    for user in users:
        email_api.send_email(user=user, header='天气提醒', text=get_wether_remind())

def call():
    wether_forecast()
    wether_remind()
