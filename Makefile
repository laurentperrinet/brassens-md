default: compile

install:
	npm i -g markdown-it-music

assemble:
	python3 build.py

compile:
	python3 build.py --render

publish: compile
	git add -A docs songs && git commit -m'update' ; git push
