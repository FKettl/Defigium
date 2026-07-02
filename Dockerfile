FROM python:3.11-slim

# Install basic system utilities if your script needs them (compiled extensions, curl, etc.)
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# Copy your dependency manifest first to take advantage of Docker layer caching
COPY requirements.txt* /app/

# Install dependencies if requirements.txt exists
RUN if [ -f "requirements.txt" ]; then pip install --no-cache-dir -r requirements.txt; fi

# (Optional) If you don't use -v mounting, uncomment the line below to hard-copy code into the image:
# COPY . /app
