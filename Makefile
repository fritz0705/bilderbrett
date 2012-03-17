SASS := sass

.PHONY: all clean
all: static/style.css

%.css: %.scss
	$(SASS) $^ $@

clean:
	rm -rf .sass-cache static/style.css
