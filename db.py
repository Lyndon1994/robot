# -*- coding: utf-8 -*-
import sqlite3,os

conn = sqlite3.connect('%s/rss.db' % os.path.split(os.path.realpath(__file__))[0])
cursor = conn.cursor()