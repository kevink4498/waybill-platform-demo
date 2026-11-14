.PHONY: test lint render validate fmt

test:            ## run unit tests for both services
	cd services/ingest-api && pytest -q
	cd services/tracker-worker && pytest -q

lint:            ## lint Python, shell and the chart
	ruff check services
	shellcheck scripts/*.sh
	helm lint charts/microservice --set image.tag=main-0000000

render:          ## print what Flux would apply to an environment: make render ENV=dev
	kubectl kustomize gitops/apps/overlays/$(ENV)

validate:        ## terraform fmt + validate for every environment
	terraform fmt -check -recursive terraform
	for e in dev staging prod; do terraform -chdir=terraform/envs/$$e init -backend=false -input=false >/dev/null && terraform -chdir=terraform/envs/$$e validate; done

fmt:
	terraform fmt -recursive terraform
	ruff check services --fix
