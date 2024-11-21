# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Install sqlite3
RUN apt-get update && apt-get install -y sqlite3

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Remove the existing database file if it exists
RUN rm -f voting.db

# Run the database setup script
RUN python createdb.py

# Expose port 5000 for the application
EXPOSE 5000

# Define the command to run the application
CMD ["python", "app.py"]