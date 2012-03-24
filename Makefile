SASS := sass
CONVERT := convert
THUMB_SIZE := 200

.PHONY: all deploy thumbnails clean mrproper stylesheets
all: deploy

deploy:
	mkdir -p files/
	mkdir -p thumbnails/

thumbnails: deploy
	for file in $$(ls files/); \
	do \
		$(CONVERT) files/$$file -resize $(THUMB_SIZE) thumbnails/$$file; \
	done;

clean:
	rm -rf .sass-cache static/style.css

mrproper: clean
	git clean -fdx

stylesheets: static/style.css

%.css: %.scss
	$(SASS) $(SASSFLAGS) $^ $@

