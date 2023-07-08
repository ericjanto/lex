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
testall:
	pytest
testlf:
	pytest --lf -vv
