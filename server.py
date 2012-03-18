#!/usr/bin/env python3
# coding: utf-8

import configparser

import bilderbrett
from bilderbrett import app
import tornado.ioloop, tornado.httpserver, tornado.httpserver

if __name__ == '__main__':
	config = configparser.ConfigParser()
	config.read("production.ini")

	if not "database" in config or not "url" in config["database"]:
		exit(1)

	bilderbrett.session = bilderbrett.setup_database(config["database"]["url"])

	sock = None
	if "server" in config and "socket" in config["server"]:
		sock = tornado.netutil.bind_unix_socket(config["server"]["socket"])
	else:
		sock = tornado.netutil.bind_unix_socket("bilderbrett.sock")

	server = tornado.httpserver.HTTPServer(app)
	server.add_sockets([sock])
	tornado.ioloop.IOLoop.instance().start()
