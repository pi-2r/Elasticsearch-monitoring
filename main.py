__author__ = 'zen'
# !/usr/bin/env python
# -*- coding: utf-8 -*-

import smtplib
import sys
import os
import re
import socket
import httplib
import time
from datetime import datetime
from daemon import runner
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

# class that apporate several action on your cluster
class ESAction():

    @staticmethod
    def restart_es():
        os.system("/etc/init.d/elasticsearch restart")
        # os.system("touch logRestart"+str(Num))
        # os.system("date > logRestart"+str(Num))

    def get_link_status(self, url):
        """
        Gets the HTTP status of the url or returns an error associated with it.  Always returns a string.
        """
        print url
        https = False
        url = re.sub(r'(.*)#.*$', r'\1', url)
        url = url.split('/', 3)
        if len(url) > 3:
            path = '/'+url[3]
        else:
            path = '/'
        if url[0] == 'http:':
            port = 80
        elif url[0] == 'https:':
            port = 443
            https = True
        if ':' in url[2]:
            host = url[2].split(':')[0]
            port = url[2].split(':')[1]
        else:
            host = url[2]
        try:
            print "toto"
            headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:26.0) Gecko/20100101 Firefox/26.0',
                       'Host': host}
            if https:
                conn = httplib.HTTPSConnection(host=host, port=port, timeout=10)
            else:
                conn = httplib.HTTPConnection(host=host, port=port, timeout=10)
            conn.request(method="HEAD", url=path, headers=headers)
            response = str(conn.getresponse().status)
            conn.close()
        except socket.gaierror, e:
            response = "Socket Error (%d): %s" % (e[0], e[1])
        except StandardError, e:
            if hasattr(e, 'getcode') and len(e.getcode()) > 0:
                response = str(e.getcode())
            if hasattr(e, 'getcode') and len(e.getcode()) > 0:
                response = str(e.getcode())
            if hasattr(e, 'message') and len(e.message) > 0:
                response = str(e.message)
            elif hasattr(e, 'msg') and len(e.msg) > 0:
                response = str(e.msg)
            elif type('') == type(e):
                response = e
            else:
                response = "Exception occurred without a good error message." \
                         "Manually check the URL to see the status. If it is believed " \
                         "this URL is 100% good then file a issue for a potential bug."
        return response

# Class that send e-mail with your Google account
class SendMail():

    def __init__(self, password, email, smtp, port):
        """"
        Constructor:
            contains all the information about the
            password, the original mail address of the SMTP
            and the port.

        :arg password: mailbox password.
        :arg email: email.
        :arg smtp: stmp server.
        :arg port: port.
        """
        self.msg = MIMEMultipart()
        self._password = password
        self._email = email
        self._smtp = smtp
        self._port = port


    def send_email(self, from_user, to, subject, message):
        """
        Method for sending one email.

        :arg from_user: adresse mail de l'envoyer.
        :arg to: adresse mail du destinataire.
        :arg subject: sujet du mail.
        :arg message: corps du message.
        """

        self.msg['From'] = from_user
        self.msg['To'] = to
        self.msg['Subject'] = subject
        self.msg.attach(MIMEText(message))
        mailserver = smtplib.SMTP(self._smtp, self._port)
        mailserver.ehlo()
        mailserver.starttls()
        mailserver.ehlo()
        mailserver.login(self._email, self._password)
        mailserver.sendmail(from_user, to, self.msg.as_string())
        mailserver.quit()

# Class that launch a deamon in order to monitor a PID
class Monitoring():

    def __init__(self):
        """
        Constructor:
            contains all stdin/stdout/stderr path,
            the path where the PID deamon will be stored,
            and the call at the other class.

        :arg pid: PID.
        """
        self.pid_name = 'my_monitoring.pid'
        self.stdin_path = '/dev/null'
        self.stdout_path = '/dev/tty'
        self.stderr_path = '/dev/tty'
        self.pidfile_path = '/tmp/'+self.pid_name
        self.limit_fd = 1
        self.sleep_time = 180
        self.pidfile_timeout = 5
        self._ip_cluster = ['http://127.0.0.1']
        self.es_action = ESAction()
        self.mail = SendMail("$password", "$email", "smtp.gmail.com", "587")
        self.message = None

    @staticmethod
    def date_today():
        d = datetime.now()
        now = str(d.day)+"-"+str(d.month)+"-"+str(d.year)+" "+str(d.hour)+":"+str(d.minute)+":"+str(d.second)
        return now

    def start_notify(self):
        """
        Method that notify by mail the beginning of the monitoring.
        """
        # We read the PID of py-daemon
        file = open(self.pidfile_path, 'r')
        self.message = "Deamon PID: " + file.read()
        self.mail.send_email("localhost", "$your_email", "[my_monitoring] Start Monitoring", self.message)
        self.message = None

    def alert_notify(self):
        """
        Method that notify by mail the alert of the monitoring.
        """
        self.message = "ElasticSearch has been restarted at " + self.date_today()
        self.mail.send_email("localhost", "$your_email", "[my_monitoring] Alert", self.message)
        self.message = None

    def run(self):
        """
        Main method that monitor the PID
        """
        # self.start_notify()

        try:
            while True:
                for ip in self._ip_cluster:
                    if self.es_action.get_link_status(ip) != "200":
                        self.es_action.restart_es()
                time.sleep(self.sleep_time)

        except Exception, e:
            self.message = "[Error]: ", e
            print e
            sys.exit(0)

# Main
if __name__ == '__main__':
    # Check if the programme can read and write in the tmp folder
    ret = os.access("/tmp/", os.R_OK)
    ret2 = os.access("/tmp/", os.W_OK)
    if os.getuid() == 0:
        if ret and ret2:
            daemon = runner.DaemonRunner(Monitoring())
            daemon.do_action()
        else:
            print "[Error] Please to check the read/write permissions of 'tmp' folder"
    else:
            print "[Error] This script must be run as root"
    sys.exit(0)