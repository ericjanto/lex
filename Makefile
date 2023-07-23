.PHONY: apidev apiprod apidocs apischema dbdev dbprod dbdevadd setup setupvalidate testall testlf
.DEFAULT_GOAL := apiprod

PYTHON ?= python3
BASE_VOCAB_PATH ?= backend/assets/reference-vocabulary/vocabulary.base.txt


apidev:
	uvicorn backend.api:app --reload
apiprod:
	gunicorn --workers 9 --timeout 120 -k uvicorn.workers.UvicornWorker backend.api:app
apidocs:
	open http://127.0.0.1:8000/docs
apischema:
	open http://127.0.0.1:8000/openapi.json
dbdev:
	pscale shell lex development
dbprod:
	pscale shell lex main
dbdevadd:
	cp $(BASE_VOCAB_PATH) t.txt
	rm $(BASE_VOCAB_PATH)
	touch $(BASE_VOCAB_PATH)
	(cd backend; $(PYTHON) cli.py add assets/dev-samples/harry-potter-small-1.txt)
	(cd backend; $(PYTHON) cli.py add assets/dev-samples/harry-potter-small-2.txt)
	(cd backend; $(PYTHON) cli.py add assets/dev-samples/harry-potter-small-3.txt)
	cp t.txt $(BASE_VOCAB_PATH)
	rm t.txt
bsetup:
	conda config --set auto_activate_base False
	conda env create -f backend/environment.yml
	conda activate lex
	(cd backend; mypy --install-types)
	@$(MAKE) bsetupvalidate
bsetupvalidate:
	$(PYTHON) -m spacy validate
fdev:
	(cd frontend; pnpm run dev)
