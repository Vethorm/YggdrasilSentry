# Use the official Python image as the base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the project code into the container
COPY . /app

RUN ls

# Install the project dependencies
RUN pip install --no-cache-dir .

# Set the default command to run the application
CMD ["sentrybot"]