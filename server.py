#!/usr/bin/env python3
# coding: utf-8

from bilderbrett import app
import tornado.ioloop, tornado.httpserver, tornado.httpserver

if __name__ == '__main__':
	sock = tornado.netutil.bind_unix_socket("./bilderbrett.sock")
	server = tornado.httpserver.HTTPServer(app)
	server.add_sockets([sock])
	tornado.ioloop.IOLoop.instance().start()
