.PHONY: apidev apiprod apidocs apischema dbdev dbprod setup setupvalidate testall testlf

PYTHON=python3

apidev:
	uvicorn api:app --reload
apiprod:
	gunicorn -k uvicorn.workers.UvicornWorker
apidocs:
	open http://127.0.0.1:8000/docs
apischema:
	open http://127.0.0.1:8000/openapi.json
dbdev:
	pscale shell lex development
dbprod:
	pscale shell lex production
setup:
	conda config --set auto_activate_base False
	conda env create -f environment.yml
	conda activate lex
	mypy --install-types
	@$(MAKE) setupvalidate
setupvalidate:
	$(PYTHON) -m spacy validate
testall:
	pytest
testlf:
	pytest --lf -vv
