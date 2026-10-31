default: compile

assemble:
	python3 assembler.py

# chord diagrams of accords/, from the `Accords :` blocks of the songs
diagrammes:
	python3 diagrammes_accords.py

# checks the songs against the ChordPro notation; `make valide PRO=dossier` also writes strict .pro files
valide:
	python3 chordpro_valider.py $(if $(PRO),--pro $(PRO),)

compile:
	python3 assembler.py --rendre

# the site itself is built and deployed on GitHub by .github/workflows/pages.yml
publie:
	git add -A chansons accords assembler.py rendre.py diagrammes_accords.py .github && git commit -m'update' ; git push
