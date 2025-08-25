ALEMBIC_INI=src/infrastructure/database/alembic.ini

.PHONY: setup-env
setup-env:
	@sed -i '' "s/^BOT_SECRET_TOKEN=.*/BOT_SECRET_TOKEN=$(shell openssl rand -hex 64)/" .env
	@sed -i '' "s/^DATABASE_PASSWORD=.*/DATABASE_PASSWORD=$(shell openssl rand -hex 24)/" .env
	@sed -i '' "s/^REDIS_PASSWORD=.*/REDIS_PASSWORD=$(shell openssl rand -hex 24)/" .env
	@sed -i '' "s/^APP_CRYPT_KEY=.*/APP_CRYPT_KEY=$(shell openssl rand -base64 32)/" .env
	@echo "Secrets updated. Check your .env file"

.PHONY: migration
migration:
ifndef message
	$(error message is undefined. Use: make migration message="Your message")
endif
	alembic -c $(ALEMBIC_INI) revision --autogenerate -m "$(message)"

.PHONY: migrate
migrate:
	alembic -c $(ALEMBIC_INI) upgrade head

.PHONY: downgrade
downgrade:
ifndef rev
	$(error rev is undefined. Use: make downgrade rev=<revision>)
endif
	alembic -c $(ALEMBIC_INI) downgrade $(rev)

.PHONY: run
run:
	@docker compose up -d --build
	@docker compose logs -f

.PHONY: run-dev
run-dev:
	@docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
	@docker compose logs -f

.PHONY: run-local
run-local:
	@docker compose -f docker-compose.local.yml up --build
	@docker compose logs -f