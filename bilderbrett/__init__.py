# coding: utf-8

from tornado.web import Application, StaticFileHandler, FallbackHandler
from tornado.wsgi import WSGIContainer
from sqlalchemy import create_engine, asc, desc, and_, or_
from sqlalchemy.orm import sessionmaker
from bilderbrett.tables import Board, Post, Attachment, Base
from datetime import datetime

import bottle
from bottle import jinja2_template as template, route

engine, session = None, None
chunksize = 4096
"""
engine = create_engine("postgresql://fritz@/bilderbrett")
Session = sessionmaker(bind=engine)
session = Session(autocommit=True)

Base.metadata.create_all(engine)
"""

def setup_database(engine_url=None, **kwargs):
	if engine_url:
		engine = create_engine(engine_url)
	Base.metadata.create_all(engine)
	Session = sessionmaker(bind=engine)
	return Session(autocommit=True, **kwargs)

def save_files(post, files):
	import re
	for filename in files:
		file = files[filename]
		type = file.filename.split(".")[-1].lower()
		is_image = False

		if re.match(r'(jpg|png|jpeg|gif)', type):
			is_image = True

		attachment = Attachment(
				name=file.filename,
				type=type,
				is_image=is_image,
				post_id=post.id
			)
		session.add(attachment)
		session.flush()
		
		with open("files/{0}.{1}".format(attachment.id, attachment.type), "w+b") as fd:
			fd.write(file.value)
			fd.close()

@route("/<board:re:[a-z]+>/")
@route("/<board:re:[a-z]+>/<page:int>")
def show_board(board, page=0):
	if page >= 10 or page < 0:
		bottle.abort(403)
	board = session.query(Board).filter_by(id=board).first()
	if board == None:
		bottle.abort(404)
	threads = session.query(Post).filter_by(board_id=board.id, is_thread=True).order_by(desc(Post.last_post_time)).limit(5).offset(page * 5)

	return template("board", threads=threads, board=board, page=page, pages=[i for i in range(10)])

@route("/<board:re:[a-z]+>/", method="POST")
def new_thread(board):
	board = session.query(Board).filter_by(id=board).first()
	if board == None:
		bottle.abort(404)

	session.begin()
	time = datetime.now()
	post = Post(
			title=bottle.request.forms.subject,
			author=board.default_nick,
			content=bottle.request.forms.content,
			is_thread=True,
			board_id=board.id,
			time=datetime.now(),
			last_post_time=datetime.now(),
			sage=bool(bottle.request.forms.sage)
		)
	if board.allow_nicks and bool(bottle.request.forms.name):
		post.author = bottle.request.forms.name
	session.add(post)
	session.flush()

	save_files(post, bottle.request.files)
	session.commit()

	bottle.redirect("/{0}/thread-{1}".format(board.id, post.id))

@route("/<board:re:[a-z]+>/thread-<thread:int>")
def show_thread(board, thread):
	board = session.query(Board).filter_by(id=board).first()
	if board == None:
		bottle.abort(404)

	thread = session.query(Post).filter_by(id=thread, is_thread=True).first()
	if thread == None:
		bottle.abort(404)

	posts = session.query(Post).filter_by(thread_id=thread.id)

	return template("thread", board=board, thread=thread, posts=posts)

@route("/<board:re:[a-z]+>/thread-<thread:int>", method="POST")
def new_post(board, thread):
	board = session.query(Board).filter_by(id=board).first()
	if board == None:
		bottle.abort(404)

	thread = session.query(Post).filter_by(id=thread, is_thread=True).first()
	if thread == None:
		bottle.abort(404)

	session.begin()

	time = datetime.now()
	post = Post(
			title=bottle.request.forms.subject,
			author=board.default_nick,
			content=bottle.request.forms.content,
			is_thread=False,
			time=time,
			board_id=board.id,
			thread_id=thread.id,
			sage=bool(bottle.request.forms.sage)
		)
	if board.allow_nicks and bool(bottle.request.forms.name):
		post.author = bottle.request.forms.name
	if not post.sage:
		thread.last_post_time = time
	session.add(thread)
	session.add(post)
	session.flush()

	save_files(post, bottle.request.files)

	session.commit()
	bottle.redirect("/{0}/thread-{1}".format(board.id, thread.id))

@route("/")
def index():
	boards = session.query(Board)
	return template("index", boards=boards)

bottle_app = WSGIContainer(bottle.app())
app = Application([
	(r'/static/(.*)', StaticFileHandler, dict(path="static/")),
	(r'/files/(.*)', StaticFileHandler, dict(path="files/")),
	(r'/.*', FallbackHandler, dict(fallback=bottle_app))
])
