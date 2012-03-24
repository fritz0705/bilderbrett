SASS := sass
CONVERT := convert
THUMB_SIZE := 200

.PHONY: all clean thumbnails
all: static/style.css

thumbnails:
	for file in $$(ls files/); do $(CONVERT) files/$$file -resize $(THUMB_SIZE) thumbnails/$$file; done

%.css: %.scss
	$(SASS) $(SASSFLAGS) $^ $@

clean:
	rm -rf .sass-cache static/style.css
