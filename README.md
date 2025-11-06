Luxurious Earths - Flask CRUD Project
-------------------------------------
Folder: NEED
- app.py           -> main Flask application
- config.py        -> database configuration
- requirements.txt -> Python dependencies
- templates/       -> Jinja2 HTML templates
- static/          -> static assets (imgs folder should be placed inside static/imgs)

Database:
- This project expects a MySQL database named 'mymenu' with tables as described by the user.
- Update config.py with your local MySQL credentials if needed.

Run:
$ python3 -m venv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
$ export FLASK_APP=app.py
$ flask run
