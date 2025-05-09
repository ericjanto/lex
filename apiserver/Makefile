.DEFAULT_GOAL := server

.PHONY: server
server:
	gunicorn --workers 9 --timeout 120 -k uvicorn.workers.UvicornWorker api.index:app

.PHONY: serverdev
serverdev:
	uvicorn api.index:app --reload

.PHONY: apidocs
apidocs:
	open http://127.0.0.1:8000/docs

.PHONY: apischema
apischema:
	open http://127.0.0.1:8000/openapi.json
