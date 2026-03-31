install:
	python -m pip install --upgrade pip
	python -m pip install -r requirements-dev.txt

run:
	uvicorn app.main:app --reload

test:
	pytest