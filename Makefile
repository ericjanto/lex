.PHONY: fdev
fdev:
	(cd frontend; pnpm run dev)

.PHONY: psql
psql:
	psql -h db.ldmdsjurxfaefuehqezh.supabase.co -d postgres -U postgres

.PHONY: pre
pre:
	pre-commit run -a --hook-stage manual
