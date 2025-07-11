FROM debian:bullseye-slim

# Install dependencies
RUN apt-get update && \
    apt-get install -y lm-sensors fancontrol smartmontools python3 python3-pip procps && \
    apt-get clean

# Install Flask
RUN pip3 install flask

# Copy app code
COPY app /app
WORKDIR /app

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Set the container entrypoint
ENTRYPOINT ["./entrypoint.sh"]


