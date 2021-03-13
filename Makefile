default: compile

install:
	npm i -g markdown-it-music

compile:
	python3 brassens.py
	musicmd brassens_mm.md -o index.html
