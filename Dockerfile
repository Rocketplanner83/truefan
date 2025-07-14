FROM debian:bullseye-slim

# Install dependencies
RUN apt-get update && \
    apt-get install -y \
        lm-sensors \
        fancontrol \
        smartmontools \
        python3 \
        python3-pip \
        procps \
    && apt-get clean

# Install Python packages
RUN pip3 install flask psutil gunicorn

# Copy app and entrypoint
COPY app /app
COPY entrypoint.sh /app/entrypoint.sh

WORKDIR /app
RUN chmod +x entrypoint.sh

# Set ENTRYPOINT correctly
ENTRYPOINT ["./entrypoint.sh"]
