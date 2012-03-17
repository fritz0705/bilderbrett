#!/usr/bin/env python3
# coding: utf-8

from bilderbrett import app
import tornado.ioloop

if __name__ == '__main__':
	app.listen(65002)
	tornado.ioloop.IOLoop.instance().start()
