.PHONY: setup up rebuild down logs logs-backend test demo seed clean urls \
        ollama-pull-llm ollama-pull-embed ollama-pull-vision ollama-list

## First-time setup
setup:
	bash setup.sh

## Start all services
up:
	docker compose up -d

## Rebuild images and start (use after code changes)
rebuild:
	docker compose up -d --build

## Stop all services
down:
	docker compose down

## View all logs
logs:
	docker compose logs -f

## Backend logs only
logs-backend:
	docker compose logs -f backend

## Run test suite
test:
	cd backend && python -m pytest tests/ -v

## Generate the synthetic demo PDF
demo:
	python3 scripts/generate_demo_manual.py

## Seed demo equipment + upload manual
seed:
	@echo "Seeding demo data..."
	@EQ_ID=$$(curl -sf -X POST http://localhost:8000/api/v1/equipment/ \
		-H "Content-Type: application/json" \
		-d '{"manufacturer":"Demo Corp","model":"MX-400","equipment_type":"Motor Drive"}' \
		| python3 -c "import sys,json; print(json.load(sys.stdin)['id'])") && \
	curl -sf -X POST http://localhost:8000/api/v1/documents/upload \
		-F "file=@demo-data/MX400-Maintenance-Manual-DEMO.pdf" \
		-F "title=MX-400 Maintenance Manual (DEMO)" \
		-F "equipment_id=$$EQ_ID" > /dev/null && \
	echo "Done. Equipment id: $$EQ_ID"

## Reset everything (wipes DB + vectors + Ollama models)
clean:
	docker compose down -v
	@echo "All volumes removed."

## Show service URLs
urls:
	@echo "App:        http://localhost:3000"
	@echo "API docs:   http://localhost:8000/docs"
	@echo "Qdrant UI:  http://localhost:6333/dashboard"
	@echo "Ollama:     http://localhost:11434"

# ── Ollama model management ────────────────────────────────────────────────

## Pull the configured LLM (set MODEL= to override, e.g. make ollama-pull-llm MODEL=mistral)
ollama-pull-llm:
	docker compose exec ollama ollama pull $(or $(MODEL),llama3.2)

## Pull a recommended embedding model
ollama-pull-embed:
	docker compose exec ollama ollama pull $(or $(MODEL),nomic-embed-text)

## Pull a recommended vision model (for image fault code extraction)
ollama-pull-vision:
	docker compose exec ollama ollama pull $(or $(MODEL),llava)

## List downloaded Ollama models
ollama-list:
	docker compose exec ollama ollama list

## Interactive Ollama shell (test a model directly)
ollama-run:
	docker compose exec -it ollama ollama run $(or $(MODEL),llama3.2)
