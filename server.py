#!/usr/bin/env python3
# coding: utf-8

import configparser
import os
import sys

import bilderbrett
from bilderbrett import app
import tornado.ioloop, tornado.httpserver

if __name__ == '__main__':
	config = configparser.ConfigParser()
	config.read("production.ini")

	bilderbrett.setup_database(config.get("database", "url", fallback="sqlite:///production.db"))
	sock = tornado.netutil.bind_unix_socket(config.get("server", "socket", fallback="bilderbrett.sock"))

	if config.getboolean("server", "daemon", fallback=False):
		pid = os.fork()
		if pid != 0:
			with open(config.get("server", "pidfile", fallback="bilderbrett.pid"), "w") as file:
				file.write(str(pid))
				file.write("\n")
			sys.exit(0)
		null = open("/dev/null", "w+")
		os.close(0)
		os.dup2(null.fileno(), 0)
		os.close(1)
		os.dup2(null.fileno(), 1)
		os.close(2)
		os.dup2(null.fileno(), 2)
		os.setsid()

	server = tornado.httpserver.HTTPServer(app)
	server.add_sockets([sock])
	tornado.ioloop.IOLoop.instance().start()
