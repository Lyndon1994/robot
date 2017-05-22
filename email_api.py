# -*- coding: utf-8 -*-
import config
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr
import smtplib
import logging

FORMAT = '%(asctime)-15s %(levelname)s:%(module)s:%(message)s'
logging.basicConfig(level=logging.INFO, format=FORMAT)


def send_email(user, header, text, subtype='plain'):
    def _format_addr(s):
        name, addr = parseaddr(s)
        return formataddr((Header(name, 'utf-8').encode(), addr))

    from_addr = config.EMAIL_FROM
    password = config.EMAIL_PASSWORD
    smtp_server = config.EMAIL_SERVER

    msg = MIMEText(text, subtype, 'utf-8')
    msg['From'] = _format_addr('%s <%s>' % (config.EMAIL_FROM_NAME, from_addr))
    msg['To'] = _format_addr('%s <%s>' % (user[0], user[1]))
    msg['Subject'] = Header(header, 'utf-8').encode()

    server = smtplib.SMTP(smtp_server, 25)
    server.starttls()
    server.login(from_addr, password)
    server.sendmail(from_addr, [user[1]], msg.as_string())
    server.quit()
    logging.info('成功给%s <%s>发送一封邮件【%s】' % (user[0], user[1], header))
