# api-address

Hey! 👋 This is a small address book API built with FastAPI. You can use it to create, update and delete addresses, and to find addresses within a given distance of a location.

There are two ways to run it. Pick whichever is easier for you.

---

## Option 1: Run it locally

You'll need **Python 3.12+** and **[Poetry](https://python-poetry.org/docs/#installation)** installed.

**1. Clone the repo and go into the folder**

```bash
git clone <repository-url> api-address
cd api-address
```

**2. Set up the virtual environment**

This makes Poetry create the `.venv` folder inside the project, so everything stays in one place:

```bash
poetry config virtualenvs.in-project true
```

**3. Install the dependencies**

```bash
poetry install
```

**4. Create the database tables**

This runs the migrations and creates a local SQLite database (`api_address.db`):

```bash
poetry run alembic upgrade head
```

**5. Start the server**

```bash
poetry run uvicorn app.main:app --reload
```

That's it! Open **<http://localhost:8000/docs>** in your browser and you'll see the Swagger page where you can try out the endpoints.

To stop the server, press `Ctrl + C`.

---

## Option 2: Run it with Docker

If you have Docker installed, you don't need Python or Poetry at all. Just run:

```bash
docker compose up --build -d
```

This builds the image, sets up the database and starts the API in the background. Give it a few seconds, then open **<http://localhost:8000/docs>**.

When you're done, stop it with:

```bash
docker compose down
```

> Heads up: with Docker the database lives inside the container, so your data is wiped when you run `docker compose down`.

---

## Having trouble?

- **`poetry: command not found`**: Poetry isn't installed or isn't on your PATH. Follow the [install guide](https://python-poetry.org/docs/#installation).
- **Errors saying a table doesn't exist**: you probably skipped step 4. Run `poetry run alembic upgrade head` and try again.
- **Port 8000 is already in use**: run the server on another port with `poetry run uvicorn app.main:app --reload --port 8080`.

If you're still stuck, just ping me. Happy testing! 🚀
