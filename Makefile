.PHONY: bootstrap db-up db-down db-migrate dev-infra dev format lint typecheck test test-unit test-integration test-e2e test-security test-mutation verify build deploy-local smoke-test backup restore rollback

bootstrap:
	corepack pnpm bootstrap

db-up:
	corepack pnpm db:up

db-down:
	corepack pnpm db:down

db-migrate:
	corepack pnpm db:migrate

dev-infra:
	corepack pnpm dev-infra

dev:
	corepack pnpm dev

format:
	corepack pnpm format

lint:
	corepack pnpm lint

typecheck:
	corepack pnpm typecheck

test:
	corepack pnpm test

test-unit:
	corepack pnpm test:unit

test-integration:
	corepack pnpm test:integration

test-e2e:
	corepack pnpm test:e2e

test-security:
	corepack pnpm test:security

test-mutation:
	corepack pnpm test:mutation

verify:
	corepack pnpm verify

build:
	corepack pnpm build

deploy-local:
	corepack pnpm deploy:local

smoke-test:
	corepack pnpm smoke:test

backup:
	corepack pnpm backup

restore:
	corepack pnpm restore

rollback:
	corepack pnpm rollback
