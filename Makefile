build:
	python ./scripts/build.py

check:
	twine check dist/*

install:
	pip install -e .[dev]

setup: clean install

clean:
	rm -rf build dist *.egg-info

freeze:
	pip freeze > requirements.txt

test:
	cd tests && pytest --cov=prich --cov-report=term && cd ..
