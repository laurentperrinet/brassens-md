default: compile

install:
	npm i -g markdown-it-music

format:
	python3 brassens.py

compile: format
	musicmd brassens_mm.md -o index.html
