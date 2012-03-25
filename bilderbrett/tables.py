# coding: utf-8

from sqlalchemy import MetaData, Table, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

metadata = MetaData()
Base = declarative_base()

class Board(Base):
	__tablename__ = "boards"

	id = Column(String(5), primary_key=True, nullable=False)
	title = Column(String)

	allow_nicks = Column(Boolean)
	default_nick = Column(String)
	is_public = Column(Boolean)
	pages = Column(Integer, default=10)
	description = Column(String)
	need_attachment = Column(Boolean, default=True)

class Post(Base):
	__tablename__ = "posts"

	id = Column(Integer, primary_key=True)
	title = Column(String)
	author = Column(String)
	content = Column(String, nullable=False)
	sage = Column(Boolean, default=False)
	board_id = Column(String(5), ForeignKey("boards.id"), nullable=False)
	time = Column(DateTime, nullable=False)
	thread_id = Column(Integer, ForeignKey("posts.id"))

	is_thread = Column(Boolean)
	last_post_time = Column(DateTime)
	tripcode = Column(String)

	posts = relationship("Post", order_by="Post.time")
	board = relationship("Board", backref=backref("posts"))

class Attachment(Base):
	__tablename__ = "attachments"

	id = Column(Integer, primary_key=True)
	name = Column(String, nullable=False)
	type = Column(String)
	is_image = Column(Boolean)
	post_id = Column(Integer, ForeignKey("posts.id"))

	post = relationship("Post", backref=backref("attachments"))

