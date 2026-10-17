default: compile

assemble:
	python3 assembler.py

compile:
	python3 assembler.py --rendre

# the site itself is built and deployed on GitHub by .github/workflows/pages.yml
publie:
	git add -A chansons assembler.py rendre.py .github && git commit -m'update' ; git push
