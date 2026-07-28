.PHONY: up down test seed logs

up:
	docker-compose up --build -d

down:
	docker-compose down

test:
	docker-compose exec backend pytest backend/tests

seed:
	docker-compose exec backend python backend/seed.py

logs:
	docker-compose logs -f
