# coding: utf-8

from tornado.web import Application, StaticFileHandler, FallbackHandler
from tornado.wsgi import WSGIContainer

from sqlalchemy import create_engine, asc, desc, and_, or_
from sqlalchemy.orm import sessionmaker

from bilderbrett.tables import Board, Post, Attachment, Base

import bilderbrett.templates

import subprocess
from datetime import datetime

import bottle
route = bottle.route

import jinja2

env = jinja2.Environment(loader=jinja2.FileSystemLoader("views/"))
engine, session = None, None
config = None
chunksize = 4096

def setup_database(engine_url=None, **kwargs):
	if engine_url:
		engine = create_engine(engine_url)
	Base.metadata.create_all(engine)
	Session = sessionmaker(bind=engine)
	return Session(autocommit=True, **kwargs)

def build_thumbnail(filename):
	proc = subprocess.Popen(
			[
				"convert",
				"files/" + filename + "[0]",
				"-resize",
				config.get("size", "200"),
				"thumbnails/" + filename
			],
			executable=config.get("convert", "convert")
		)

def template(name, **kwargs):
	return bilderbrett.templates.render(name, config=config, **kwargs)

def save_files(post, files):
	import re
	for filename in files:
		file = files[filename]
		type = file.filename.split(".")[-1].lower()
		is_image = False

		if re.match(r'(jpg|png|jpeg|gif|svg)', type):
			is_image = True

		attachment = Attachment(
				name=file.filename,
				type=type,
				is_image=is_image,
				post_id=post.id
			)
		session.add(attachment)
		session.flush()
		filename = "{0}.{1}".format(attachment.id, attachment.type)
		
		with open("files/" + filename, "wb") as fd:
			while True:
				chunk = file.file.read(chunksize)
				if len(chunk) == 0:
					break
				fd.write(chunk)
		if attachment.is_image:
			build_thumbnail(filename)

@route("/_resolve/<post:int>")
def resolve_post(post):
	post = session.query(Post).filter_by(id=post).first()
	if post == None:
		bottle.abort(404)
	
	if post.is_thread:
		bottle.redirect("/{0}/thread-{1}".format(post.board_id, post.id))
	else:
		bottle.redirect("/{0}/thread-{1}#{2}".format(post.board_id, post.thread_id, post.id))

@route("/<board:re:[a-z0-9]+>/")
@route("/<board:re:[a-z0-9]+>/<page:int>")
def show_board(board, page=0):
	board = session.query(Board).filter_by(id=board).first()
	if board == None:
		bottle.abort(404)
	if page >= board.pages:
		bottle.abort(403)
	threads = session.query(Post).filter_by(board_id=board.id, is_thread=True).order_by(desc(Post.last_post_time)).limit(5).offset(page * 5)
	pages_count = (session.query(Post).filter_by(board_id=board.id, is_thread=True).count() - 1) // 5 + 1
	if pages_count > board.pages:
		pages_count = board.pages
	pages = [i for i in range(pages_count)]

	return template("board", threads=threads, board=board, page=page, pages=pages)

@route("/<board:re:[a-z0-9]+>/", method="POST")
@route("/<board:re:[a-z0-9]+>/<page:int>", method="POST")
def new_thread(board, page=0):
	board = session.query(Board).filter_by(id=board).first()
	if board == None:
		bottle.abort(404)
	if 0 == len(bottle.request.files) and board.need_attachment:
		bottle.abort(403)

	session.begin()
	time = datetime.now()
	post = Post(
			title=bottle.request.forms.get('subject'),
			author=board.default_nick,
			content=bottle.request.forms.get('content'),
			is_thread=True,
			board_id=board.id,
			time=datetime.now(),
			last_post_time=datetime.now(),
			sage=bool(bottle.request.forms.get('sage'))
		)
	if board.allow_nicks and bool(bottle.request.forms.get('name')):
		post.author = bottle.request.forms.get('name')
	session.add(post)
	session.flush()

	save_files(post, bottle.request.files)
	session.commit()

	bottle.redirect("/{0}/thread-{1}".format(board.id, post.id))

@route("/<board:re:[a-z0-9]+>/thread-<thread:int>")
def show_thread(board, thread):
	board = session.query(Board).filter_by(id=board).first()
	if board == None:
		bottle.abort(404)

	thread = session.query(Post).filter_by(id=thread, is_thread=True).first()
	if thread == None:
		bottle.abort(404)

	posts = session.query(Post).filter_by(thread_id=thread.id).order_by(asc(Post.time))

	return template("thread", board=board, thread=thread, posts=posts)

@route("/<board:re:[a-z0-9]+>/thread-<thread:int>", method="POST")
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
			title=bottle.request.forms.get('subject'),
			author=board.default_nick,
			content=bottle.request.forms.get('content'),
			is_thread=False,
			time=time,
			board_id=board.id,
			thread_id=thread.id,
			sage=bool(bottle.request.forms.get('sage'))
		)
	if board.allow_nicks and bool(bottle.request.forms.get('name')):
		post.author = bottle.request.forms.get('name')
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
	boards = session.query(Board).filter_by(is_public=True)
	return template("index", boards=boards)

@route("/robots.txt")
def robots_txt():
	return 'User-Agent: *\nDisallow: /'

bottle_app = WSGIContainer(bottle.app())
app = Application([
	(r'/static/(.*)', StaticFileHandler, dict(path="static/")),
	(r'/files/(.*)', StaticFileHandler, dict(path="files/")),
	(r'/thumbnails/(.*)', StaticFileHandler, dict(path="thumbnails/")),
	(r'/.*', FallbackHandler, dict(fallback=bottle_app))
])
