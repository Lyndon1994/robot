#!/usr/bin/python3.4
# -*- coding: utf-8 -*-
# 订阅某知乎用户动态更新，发送邮件提醒

import json
from jinja2 import Template
import time, requests
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr
import os
from zhihu import config
import smtplib
import lxml.html
from pymongo import MongoClient

import logging

FORMAT = '%(asctime)-15s %(levelname)s:%(module)s:%(message)s'
logging.basicConfig(level=logging.INFO, format=FORMAT)

IOS_USER_AGENT = 'Mozilla/5.0 (iPhone; CPU iPhone OS 9_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13B143 Safari/601.1'
FF_USER_AGENT = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:53.0) Gecko/20100101 Firefox/53.0'


class ListenZhihu():
    def __init__(self, client=None):
        self.client = MongoClient('mongodb://%s:%s@%s' % (
            config.MONGO_USER, config.MONGO_PASSWORD, config.MONGO_HOST)) if client is None else client
        self.db = self.client.zhihu

    def get_activity(self, activity_id):
        return self.db.activities.find_one({'_id': activity_id})

    def remind(self, item):
        try:
            self.send_email(item)
            item['_id'] = item['id']
            self.db.activities.insert_one(item)
        except:
            pass

    def listen_activities(self, url='https://www.zhihu.com/people/wei-jing-ji-44/activities'):
        headers = {'user-agent': FF_USER_AGENT}
        r = requests.get(url, headers=headers)
        tree = lxml.html.fromstring(r.content)
        data = tree.cssselect('div#data')
        if data:
            data_state = data[0].attrib['data-state']
            data_state_obj = json.loads(data_state)
            activities = data_state_obj['entities']['activities']
            for activity_id, activity_data in activities.items():
                if self.get_activity(activity_id) is None:
                    logging.info('读取到一条新动态...')
                    item = {}
                    item['id'] = activity_id
                    item['action_text'] = activity_data['actionText']
                    item['created_time'] = activity_data['createdTime']
                    item['actor_name'] = activity_data['actor']['name']
                    item['actor_url'] = 'https://www.zhihu.com/people/%s/activities' % activity_data['actor'][
                        'urlToken']
                    target_id = activity_data['target']['id']
                    target_schema = activity_data['target']['schema']
                    item['schema'] = target_schema
                    if target_schema == 'answer':
                        target = data_state_obj['entities']['answers'][str(target_id)]
                        item['author'] = target['author']
                        item['title'] = target['question']['title']
                        item['content'] = target['content']
                        question_id = target['question']['id']
                        answer_id = target['id']
                        item['url'] = 'https://www.zhihu.com/question/%s/answer/%s' % (question_id, answer_id)
                        item['voteupCount'] = target['voteupCount']

                    elif target_schema == 'question':
                        target = data_state_obj['entities']['questions'][str(target_id)]
                        item['author'] = target['author']
                        item['title'] = target['title']
                        question_id = target['id']
                        item['url'] = 'https://www.zhihu.com/question/%s' % question_id
                    self.remind(item)
        else:
            logging.debug('没有获取到数据...')

    def send_email(self, item):
        def _format_addr(s):
            name, addr = parseaddr(s)
            return formataddr((Header(name, 'utf-8').encode(), addr))

        from_addr = config.EMAIL_FROM
        password = config.EMAIL_PASSWORD
        to_addr = config.EMAIL_TO
        smtp_server = config.EMAIL_SERVER

        created_time = time.strftime('%m-%d %H:%M', time.localtime(item['created_time']))
        with open('%s/remind.html' % os.getcwd()) as f:
            template = Template(f.read())
            send_data = template.render(item=item, created_time=created_time)

        msg = MIMEText(send_data, 'html', 'utf-8')
        msg['From'] = _format_addr('%s <%s>' % (config.EMAIL_FROM_NAME, from_addr))
        msg['To'] = _format_addr('%s <%s>' % (config.EMAIL_TO_NAME, to_addr))
        msg['Subject'] = Header('%s有了新动态' % item['actor_name'], 'utf-8').encode()

        server = smtplib.SMTP(smtp_server, 25)
        server.starttls()
        server.login(from_addr, password)
        server.sendmail(from_addr, [to_addr], msg.as_string())
        server.quit()
        logging.info('邮件发送成功...')


if __name__ == '__main__':
    ListenZhihu().listen_activities()
