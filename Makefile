.PHONY: apidev apiprod apidocs apischema dbdev dbprod setup setupvalidate testall testlf

PYTHON=python3

apidev:
	uvicorn backend.api:app --reload
apiprod:
	gunicorn -k uvicorn.workers.UvicornWorker backend.api:app
apidocs:
	open http://127.0.0.1:8000/docs
apischema:
	open http://127.0.0.1:8000/openapi.json
dbdev:
	pscale shell lex development
dbprod:
	pscale shell lex main
bsetup:
	conda config --set auto_activate_base False
	conda env create -f backend/environment.yml
	conda activate lex
	(cd backend; mypy --install-types)
	@$(MAKE) bsetupvalidate
bsetupvalidate:
	$(PYTHON) -m spacy validate
frontdev:
	(cd frontend; pnpm run dev)
