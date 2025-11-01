# 1. Start with a standard Python 3.10 image
FROM python:3.10-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy the requirements file and install the libraries
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy all your Python code into the container
COPY app.py .
COPY measurement_logic.py .

# 5. Tell Cloud Run what port to listen on.
ENV PORT 8080

# 6. The command to start your app using the gunicorn server.
# --- THIS IS THE FIXED LINE ---
# We use 'sh -c' to properly read the $PORT variable.
CMD sh -c "gunicorn --bind 0.0.0.0:$PORT app:app"