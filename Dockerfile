# Use an official Python runtime as the base image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy requirements.txt first to leverage Docker caching for dependencies
COPY requirements.txt . 

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create the logs directory explicitly
RUN mkdir -p /app/logs

# Copy the rest of the application code
COPY . .

# Define the default command to run the application
CMD ["python", "main.py"]
