default: publish

install:
	npm i -g markdown-it-music

format:
	python3 brassens.py

compile: format
	musicmd albums/brassens_1.md -o albums/brassens_1.html
	musicmd albums/brassens_2.md -o albums/brassens_2.html
	musicmd albums/brassens_3.md -o albums/brassens_3.html
	musicmd albums/brassens_4.md -o albums/brassens_4.html
	musicmd albums/brassens_5.md -o albums/brassens_5.html
	musicmd albums/brassens_6.md -o albums/brassens_6.html
	musicmd albums/brassens_7.md -o albums/brassens_7.html
	musicmd albums/brassens_8.md -o albums/brassens_8.html
	musicmd albums/brassens_9.md -o albums/brassens_9.html

publish: compile
	git commit -am'update' ; git push
