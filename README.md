## Setup

The first thing to do is to clone the repository:

```sh
$ git clone git clone https://yilmazdoga@bitbucket.org/e-commerce_ozu/e-commerce-backend.git
$ cd e-commerce-backend
```

Create a virtual environment to install dependencies in and activate it:

```sh
$ python3 -m venv venv
$ source venv/bin/activate
```

Then install the dependencies:

```sh
(venv)$ pip install -r requirements.txt
```

Once `pip` has finished downloading the dependencies:
```sh
(venv)$ cd src
(venv)$ python manage.py migrate
(venv)$ python manage.py runserver
```
And navigate to `http://127.0.0.1:8000` for admin panel.

## API Endpoints

Items: `http://127.0.0.1:8000/api/items`

User Sign Up: `http://127.0.0.1:8000/rest-auth/registration/`

User Log In: `http://127.0.0.1:8000/rest-auth/login/`

See here for more info: https://django-rest-auth.readthedocs.io/en/latest/api_endpoints.html