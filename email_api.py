# -*- coding: utf-8 -*-
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr
from email.header import decode_header
from email.parser import Parser
import poplib

import config
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

# indent用于缩进显示:
def print_info(msg, indent=0):
    if indent == 0:
        for header in ['From', 'To', 'Subject']:
            value = msg.get(header, '')
            if value:
                if header == 'Subject':
                    value = decode_str(value)
                else:
                    hdr, addr = parseaddr(value)
                    name = decode_str(hdr)
                    value = u'%s <%s>' % (name, addr)
            print('%s%s: %s' % ('  ' * indent, header, value))
    if (msg.is_multipart()):
        parts = msg.get_payload()
        for n, part in enumerate(parts):
            print('%spart %s' % ('  ' * indent, n))
            print('%s--------------------' % ('  ' * indent))
            print_info(part, indent + 1)
    else:
        content_type = msg.get_content_type()
        if content_type == 'text/plain' or content_type == 'text/html':
            content = msg.get_payload(decode=True)
            charset = guess_charset(msg)
            if charset:
                content = content.decode(charset)
            print('%sText: %s' % ('  ' * indent, content + '...'))
        else:
            print('%sAttachment: %s' % ('  ' * indent, content_type))


def decode_str(s):
    # decode_header()返回一个list，
    # 因为像Cc、Bcc这样的字段可能包含多个邮件地址，
    # 所以解析出来的会有多个元素。
    # 上面的代码我们偷了个懒，只取了第一个元素。
    value, charset = decode_header(s)[0]
    if charset:
        value = value.decode(charset)
    return value

def guess_charset(msg):
    charset = msg.get_charset()
    if charset is None:
        content_type = msg.get('Content-Type', '').lower()
        pos = content_type.find('charset=')
        if pos >= 0:
            charset = content_type[pos + 8:].strip()
    return charset


def get_email():
    # 连接到POP3服务器:
    server = poplib.POP3(config.EMAIL_POP_SERVER, config.EMAIL_POP_PORT)

    # 可以打开或关闭调试信息:
    # server.set_debuglevel(1)
    # 可选:打印POP3服务器的欢迎文字:
    print(server.getwelcome().decode('utf-8'))

    # 身份认证:
    server.user(config.EMAIL_FROM)
    server.pass_(config.EMAIL_PASSWORD)

    # stat()返回邮件数量和占用空间:
    print('Messages: %s. Size: %s' % server.stat())
    # list()返回所有邮件的编号:
    resp, mails, octets = server.list()
    # 可以查看返回的列表类似[b'1 82923', b'2 2184', ...]
    print(mails)

    # 获取最新一封邮件, 注意索引号从1开始:
    index = len(mails)
    resp, lines, octets = server.retr(index)

    # lines存储了邮件的原始文本的每一行,
    # 可以获得整个邮件的原始文本:
    msg_content = b'\r\n'.join(lines).decode('utf-8')
    # 稍后解析出邮件:
    msg = Parser().parsestr(msg_content)
    print_info(msg)
    # 可以根据邮件索引号直接从服务器删除邮件:
    # server.dele(index)
    # 关闭连接:
    server.quit()
