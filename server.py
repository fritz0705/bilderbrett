#!/usr/bin/env python3
# coding: utf-8

import configparser
import argparse
import os
import sys
import signal
import errno

import bilderbrett
from bilderbrett import app
import tornado.ioloop, tornado.httpserver

argparser = argparse.ArgumentParser()

argparser.add_argument('action', choices=("start", "stop", "status", "restart"))
argparser.add_argument('--daemon', '-d', action='store_true')
argparser.add_argument('--config', '-c',
		default="production.ini",
		action="store",
		help="set configuration file")

def stop_server(config):
	if not config.getboolean("server", "daemon", fallback=False):
		sys.stderr.write("Assertion failed: server.daemon == True\n")
		sys.exit(1)
	
	pidfile = open(config.get("server", "pidfile", fallback="bilderbrett.pid"), "r")
	pid = int(pidfile.read())

	os.kill(pid, signal.SIGINT)

def start_server(config):
	socket = config.get("server", "address", fallback="@bilderbrett.sock")
	socks = []
	
	if socket[0] == '@':
		mode = int(config.get("server", "mode", fallback="0666"), 8)
		socks = [ tornado.netutil.bind_unix_socket(socket[1:], mode=mode) ]
	else:
		port = config.getint("server", "port", fallback=8080)
		socks = tornado.netutil.bind_sockets(port, socket)

	if config.getboolean("server", "daemon", fallback=False):
		try:
			pidfile = open(config.get("server", "pidfile", fallback="bilderbrett.pid"))
			pid = int(pidfile.read())
			os.kill(pid, 0)
		except IOError as e:
			if e.errno != errno.ENOENT:
				sys.stderr.write("An error occured while checking the pidfiled: {0}\n".format(e.strerror))
				os.exit(1)
		except OSError as e:
			if e.errno != errno.ESRCH:
				sys.stderr.write("The pidfile is already in use\n")
				sys.exit(1)
		else:
			sys.stderr.write("The pidfile is already in use\n")
			sys.exit(1)

		pid = os.fork()
		if pid != 0:
			sys.stderr.write("PID: {0}\n".format(pid))
			with open(config.get("server", "pidfile", fallback="bilderbrett.pid"), "w") as file:
				file.write(str(pid))
				file.write("\n")
				file.flush()
			sys.exit(0)

		logfile = open(config.get("server", "logfile", fallback="/dev/null"), "w+")
		os.close(0)
		os.dup2(logfile.fileno(), 0)
		os.close(1)
		os.dup2(logfile.fileno(), 1)
		os.close(2)
		os.dup2(logfile.fileno(), 2)
		os.setsid()
	
	bilderbrett.session = bilderbrett.setup_database(config.get("database", "url", fallback="sqlite:///production.db"))
	bilderbrett.config = config["board"]

	def sigint_handler(signum, frame):
		sys.stderr.write("Killed with SIGINT\n")
		try:
			if config.getboolean("server", "daemon", fallback=False):
				os.unlink(config.get("server", "pidfile", fallback="bilderbrett.pid"))
		except: pass
		sys.exit(0)
	
	signal.signal(signal.SIGINT, sigint_handler)

	server = tornado.httpserver.HTTPServer(app)
	server.add_sockets(socks)
	tornado.ioloop.IOLoop.instance().start()

def restart_server(config):
	stop_server(config)
	start_server(config)

if __name__ == '__main__':
	args = argparser.parse_args()

	config = configparser.ConfigParser()
	config.read(args.config)

	if args.action == "start":
		start_server(config)
	elif args.action == "stop":
		stop_server(config)
	elif args.action == "restart":
		restart_server(config)
