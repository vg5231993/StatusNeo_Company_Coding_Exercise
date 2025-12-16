FROM python:3.11-slim
WORKDIR /app

# Copying dependency files and installing the pakcages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app /app/app
COPY lua_scripts /app/lua_scripts

# Copying the env file and renaming to .env for the pydantic-settings library to pick it up
COPY .env.dev /app/.env

# port number
EXPOSE 8000

# server run commands
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]