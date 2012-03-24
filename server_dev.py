#!/usr/bin/env python3
# coding: utf-8

import bilderbrett
from bilderbrett import app
import tornado.ioloop
from sqlalchemy import create_engine

if __name__ == '__main__':
	bilderbrett.session = bilderbrett.setup_database("sqlite:///development.db")
	bilderbrett.config = {
			"convert": "/usr/bin/convert",
			"title": "bilderbrett",
			"size": "200"
		}

	app.listen(8080)
	tornado.ioloop.IOLoop.instance().start()
