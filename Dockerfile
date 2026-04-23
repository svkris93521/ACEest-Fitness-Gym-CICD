# Use official Python runtime as base image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
#COPY . .
# copy indidividual files and directories to avoid copying unnecessary files
COPY ACEest_Fitness.py .
COPY run_ace.py .
COPY templates/ ./templates/
COPY static/ ./static/
COPY k8s/ ./k8s/
COPY aceest_fitness.db .
COPY requirements.txt .


# Expose port 5000 for Flask
EXPOSE 5000

# Use gunicorn for production grade deployment
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "ACEest_Fitness:app"]