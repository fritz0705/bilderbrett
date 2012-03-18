#!/usr/bin/env python3
# coding: utf-8

import configparser

import bilderbrett.tables
from sqlalchemy import create_engine, asc, desc, and_, or_
from sqlalchemy.orm import sessionmaker

def repair_last_post_time(session):
	threads = session.query(bilderbrett.tables.Post).filter_by(is_thread=True)

	for thread in threads:
		last_post = session.query(bilderbrett.tables.Post).filter_by(thread_id=thread.id).order_by(desc(bilderbrett.tables.Post.time)).first()
		thread.last_post_time = last_post.time
		session.add(thread)

if __name__ == '__main__':
	config = configparser.ConfigParser()
	config.read("production.ini")

	if not "database" in config or not "url" in config["database"]:
		exit(0)
	
	engine = create_engine(config["database"]["url"])
	Session = sessionmaker(engine)
	session = Session()

	bilderbrett.tables.Base.metadata.create_all(engine)

	repair_last_post_time(session)
