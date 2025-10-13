# Multi-stage build for minimal final image
FROM --platform=$TARGETPLATFORM ghcr.io/astral-sh/uv:latest AS uv

FROM --platform=$TARGETPLATFORM python:3.11-slim AS builder

# Install uv for faster dependency management
COPY --from=uv /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files and README (needed for package metadata)
COPY pyproject.toml uv.lock* README.md ./

# Copy source code (needed for building the package)
COPY src/ ./src/

# Install dependencies into a virtual environment
RUN uv sync --frozen --no-dev

# Final stage - minimal runtime image
FROM --platform=$TARGETPLATFORM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY src/ ./src/
COPY pyproject.toml ./

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Expose MCP server
# The server runs via stdio, so no port exposure needed

# Health check (optional - checks if Python and dependencies are available)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import garmin_connect_mcp; print('ok')" || exit 1

# Run the MCP server
ENTRYPOINT ["python", "-m", "garmin_connect_mcp.server"]
