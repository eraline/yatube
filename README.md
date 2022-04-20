# YATube
YATube - is a blogging platform where users can write posts, adding pictures, leave comments and follow favourite authors. 

#### Stack:
Python 3, Django 2.2, pytest, bootstrap

## How start project:
Clone a repository and go to command line:

```sh
git clone git@github.com:eraline/yatube.git
```

```sh
cd yatube
```

Create and activate virtual environment:

```sh
python3 -m venv env
```
For Windows:
```sh
source env/Scripts/activate  
```
For Linux:
```sh
source env/bin/activate  
```

Install dependencies from a file requirements.txt:

```sh
python3 -m pip install --upgrade pip
```

```sh
pip install -r requirements.txt
```

Apply migrations:

```sh
cd yatube
```
```sh
python3 manage.py migrate
```

Start project:

```sh
python3 manage.py runserver
```

URL: 
https://127.0.0.1:8000/

Admin panel:
https://127.0.0.1:8000/admin/
