# -*- coding: utf-8 -*-
import schedule,time,logging
import wether,zhihu

FORMAT = '%(asctime)-15s %(levelname)s:%(module)s:%(message)s'
logging.basicConfig(level=logging.INFO, format=FORMAT)

schedule.every(1).minutes.do(zhihu.ListenZhihu())
schedule.every().day.at("6:00").do(wether.call())
while True:
    schedule.run_pending()
    time.sleep(1)