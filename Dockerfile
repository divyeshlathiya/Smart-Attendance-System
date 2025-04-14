# Use the latest Alpine version with no vulnerabilities
FROM python:3.13-alpine

# Install required OS-level dependencies
RUN apk update && apk add --no-cache \
    build-base \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    libboost-all-dev \
    git

# Set work directory
WORKDIR /app

# Copy code
COPY . /app

# Install pip dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Run the app using gunicorn
CMD ["gunicorn", "Attendence_System.wsgi:application", "--bind", "0.0.0.0:8000"]
