.PHONY: backend frontend docker-up docker-down frontend-build backend-check

backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm install && npm run build

backend-check:
	cd backend && python -m compileall app

docker-up:
	docker compose up --build

docker-down:
	docker compose down
