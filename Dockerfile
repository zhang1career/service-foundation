FROM python:3.12-slim

WORKDIR /app

ENV TZ=Asia/Shanghai
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r service_foundation && useradd -r -g service_foundation service_foundation \
    && mkdir -p /var/log/service_foundation \
    && chown -R service_foundation:service_foundation /var/log/service_foundation \
    && chown -R service_foundation:service_foundation /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=service_foundation:service_foundation . .

# Copy and set permissions for entrypoint script
COPY --chown=service_foundation:service_foundation docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

USER service_foundation:service_foundation

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/ || exit 1

ENV LOG_DIR="/var/log/service_foundation"
ENV DJANGO_SETTINGS_MODULE="service_foundation.settings"

# Use entrypoint script
ENTRYPOINT ["/app/docker-entrypoint.sh"]
