default: publish

install:
	npm i -g markdown-it-music

format:
	python3 brassens.py

compile: format
	musicmd brassens_mm.md -o index.html

publish: compile
	git commit -am'update' ; git push
