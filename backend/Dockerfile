FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libpq-dev \
    qemu-utils \
    targetcli-fb \
    python3-rtslib-fb \
    isc-dhcp-server \
    tftpd-hpa \
    && rm -rf /var/lib/apt/lists/*

# Create application user
RUN groupadd -r ggnet && useradd -r -g ggnet ggnet

# Set work directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make entrypoint script executable
RUN chmod +x docker-entrypoint.sh

# Create necessary directories
RUN mkdir -p /opt/ggnet/{images,targets,backstores,tftp,logs,cache} && \
    chown -R ggnet:ggnet /opt/ggnet

# Set permissions
RUN chown -R ggnet:ggnet /app

# Switch to non-root user
USER ggnet

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application with entrypoint script
ENTRYPOINT ["./docker-entrypoint.sh"]