.DEFAULT_GOAL := apiguni

PYTHON ?= python3
BASE_VOCAB_PATH ?= backend/assets/reference-vocabulary/vocabulary.base.txt

.PHONY: apiuvi
apiuvi:
	uvicorn backend.api.index:app --reload

.PHONY: apiguni
apiguni:
	gunicorn --workers 9 --timeout 120 -k uvicorn.workers.UvicornWorker backend.api.index:app

.PHONY: apidocs
apidocs:
	open http://127.0.0.1:8000/docs

.PHONY: apischema
apischema:
	open http://127.0.0.1:8000/openapi.json

.PHONY: dbdev
dbdev:
	pscale shell lex development

.PHONY: dbprod
dbprod:
	pscale shell lex main

.PHONY: dbadd
dbadd:
	cp $(BASE_VOCAB_PATH) t.txt
	rm $(BASE_VOCAB_PATH)
	touch $(BASE_VOCAB_PATH)
	(cd backend; $(PYTHON) cli.py add assets/dev-samples/harry-potter-small-1.txt)
	(cd backend; $(PYTHON) cli.py add assets/dev-samples/harry-potter-small-2.txt)
	cp t.txt $(BASE_VOCAB_PATH)
	rm t.txt

.PHONY: bsetup
bsetup:
	conda config --set auto_activate_base False
	conda env create -f backend/environment.yml
	conda activate lex
	(cd backend; mypy --install-types)
	@$(MAKE) bsetupvalidate

.PHONY: bsetupvalidate
bsetupvalidate:
	$(PYTHON) -m spacy validate

.PHONY: fdev
fdev:
	(cd frontend; pnpm run dev)
