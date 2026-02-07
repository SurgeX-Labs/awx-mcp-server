FROM python:3.11-slim

LABEL org.opencontainers.image.source="https://github.com/your-org/awx-mcp-server"
LABEL org.opencontainers.image.description="AWX MCP Remote Server"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy shared package first
COPY shared/ /app/shared/
RUN pip install --no-cache-dir /app/shared/

# Copy server package
COPY server/pyproject.toml server/README.md /app/server/
COPY server/src/ /app/server/src/

# Install server
RUN pip install --no-cache-dir /app/server/

# Create non-root user
RUN useradd -m -u 1000 awxmcp && \
    chown -R awxmcp:awxmcp /app

USER awxmcp

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1

# Run server
CMD ["awx-mcp-server", "start", "--host", "0.0.0.0", "--port", "8000"]
