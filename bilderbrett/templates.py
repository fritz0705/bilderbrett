# coding: utf-8

import jinja2
import html

env = jinja2.Environment(loader=jinja2.FileSystemLoader("views/"))
arguments = {}

def render(name, **kwargs):
	return env.get_template(name + ".html").render(**kwargs)

def content_filter(content):
	import re
	content = html.escape(content.strip())
	content = re.sub(r'\[spoiler\](.*)\[/spoiler\]', r'<span class="spoiler">\1</span>', content)
	content = re.sub(r'\[i\](.*)\[/i\]', r'<i>\1</i>', content)
	content = re.sub(r'\[b\](.*)\[/b\]', r'<b>\1</b>', content)
	content = "<p>" + content.replace("\r", "").replace("\n\n", "</p><p>") + "</p>"
	return content

env.filters["format"] = content_filter
