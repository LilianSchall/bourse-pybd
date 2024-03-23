run:
	pipenv run python3 bourse.py

gun:
	pipenv run gunicorn --timeout=300 --workers=5 --threads=1 -b 127.0.0.1:8050 bourse:server
