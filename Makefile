default: publish

install:
	npm i -g markdown-it-music

format:
	python3 brassens.py

compile: format
	musicmd albums/brassens_1.md -o albums/brassens_1.html

publish: compile
	git commit -am'update' ; git push
