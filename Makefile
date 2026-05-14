.PHONY: up-postgres load-postgres psql check-postgres up-mariadb load-mariadb mariadb check-mariadb down clean-volumes

up-postgres:
	docker compose up -d postgres

load-postgres:
	docker compose run --rm loader-postgres

psql:
	docker compose exec postgres psql -U $${POSTGRES_USER:-pzero} -d $${POSTGRES_DB:-pzero}

check-postgres:
	docker compose exec -T postgres psql -U $${POSTGRES_USER:-pzero} -d $${POSTGRES_DB:-pzero} < sql/postgres/90_integrity_checks.sql

up-mariadb:
	docker compose up -d mariadb

load-mariadb:
	docker compose run --rm loader-mariadb

mariadb:
	docker compose exec mariadb mariadb -u $${MARIADB_USER:-pzero} -p$${MARIADB_PASSWORD:-pzero} $${MARIADB_DATABASE:-pzero}

check-mariadb:
	docker compose exec -T mariadb mariadb -u $${MARIADB_USER:-pzero} -p$${MARIADB_PASSWORD:-pzero} $${MARIADB_DATABASE:-pzero} < sql/mariadb/90_integrity_checks.sql

down:
	docker compose down

clean-volumes:
	docker compose down -v
