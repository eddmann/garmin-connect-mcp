# Garmin Connect MCP - Developer Documentation

This document provides comprehensive guidance for Claude Code and developers working on the Garmin Connect MCP server.

## Project Overview

A Model Context Protocol (MCP) server that provides LLMs with access to Garmin Connect health and fitness data. The server features a use-case-focused architecture with 22 tools, MCP resources, and prompts for optimal LLM integration.

**Technology Stack:**
- Python 3.11+
- FastMCP (MCP SDK)
- garminconnect library (Garmin Connect API client)
- Pydantic (data validation)
- pytest (testing)

## Development Commands

### Setup

```bash
# Install dependencies
uv sync

# Configure Garmin credentials (interactive)
uv run garmin-connect-mcp-auth

# Or manually create .env with:
# GARMIN_EMAIL=your-email@example.com
# GARMIN_PASSWORD=your-password
```

### Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/garmin_connect_mcp --cov-report=html

# Run specific test file
uv run pytest tests/test_formatters.py

# Run specific test
uv run pytest tests/test_formatters.py::test_format_distance
```

### Linting & Type Checking

```bash
# Format code with ruff
uv run ruff format .

# Lint code
uv run ruff check .

# Auto-fix linting issues
uv run ruff check --fix .

# Type check with pyright
uv run pyright
```

### Running the Server

```bash
# Run MCP server (stdio mode)
uv run garmin-connect-mcp

# Test with MCP inspector
npx @modelcontextprotocol/inspector uv run garmin-connect-mcp
```

## Code Architecture

### Project Structure

```
src/garmin_connect_mcp/
├── __init__.py
├── server.py              # FastMCP server, tool registration, resources, prompts
├── client.py              # Garmin Connect API client wrapper
├── auth.py                # OAuth authentication handling
├── cache.py               # Caching layer for API responses
├── config.py              # Configuration and environment variables
├── formatters.py          # Formatting utilities
├── pagination.py          # Pagination utilities (cursor encode/decode)
├── response_builder.py    # Structured response builder
├── time_utils.py          # Time/date parsing utilities
├── types.py               # Type definitions and Pydantic models
├── tools/                 # MCP tool implementations
│   ├── __init__.py
│   ├── activities.py      # Activity queries and details
│   ├── health_wellness.py # Health metrics, sleep, stress, heart rate
│   ├── training.py        # Training metrics and analysis
│   ├── analysis.py        # Activity comparison and similarity
│   ├── challenges.py      # Goals, PRs, badges, challenges
│   ├── devices.py         # Device management
│   ├── gear.py            # Gear/equipment tracking
│   ├── weight.py          # Weight management
│   ├── workouts.py        # Structured workouts
│   ├── data_management.py # Manual data entry
│   ├── womens_health.py   # Women's health tracking
│   └── user_profile.py    # User profile information
└── scripts/
    └── setup_auth.py      # Interactive authentication setup
```

### Key Components

#### Server (`server.py`)

- FastMCP server initialization
- Tool registration using `@mcp.tool()` decorators
- Resource registration using `@mcp.resource()` decorators
- Prompt registration using `@mcp.prompt()` decorators
- Context management for API client lifecycle

#### Client (`client.py`)

- Wrapper around `garminconnect` library
- Handles authentication and token management
- Provides high-level methods for API calls
- Token storage in `~/.garminconnect/`

#### Response Builder (`response_builder.py`)

Module for structured responses:

```python
from .response_builder import ResponseBuilder
from .pagination import build_pagination_info

# Build structured response with pagination
pagination = build_pagination_info(
    returned_count=20,
    limit=20,
    current_page=1,
    has_more=True,
    filters={"start_date": "2024-01-01"}
)

response = ResponseBuilder.build_response(
    data={"activities": [...], "summary": {...}},
    analysis={"insights": ["High training volume", ...]},
    metadata={"period": "Last 30 days"},
    pagination=pagination
)

# Response structure:
# {
#   "data": {...},       # Primary data payload
#   "analysis": {...},   # Insights and analysis
#   "pagination": {...}, # Pagination metadata (optional)
#   "metadata": {...}    # Query metadata + fetched_at timestamp
# }
```

#### Pagination (`pagination.py`)

Module for cursor-based pagination:

```python
from .pagination import encode_cursor, decode_cursor, build_pagination_info

# Encode cursor with page and filters
cursor = encode_cursor(page=2, filters={"start_date": "2024-01-01"})
# Returns: "eyJwYWdlIjoyLCJmaWx0ZXJzIjp7InN0YXJ0X2RhdGUiOiIyMDI0LTAxLTAxIn19"

# Decode cursor
cursor_data = decode_cursor(cursor)
# Returns: {"page": 2, "filters": {"start_date": "2024-01-01"}}

# Build pagination info for response
pagination = build_pagination_info(
    returned_count=20,
    limit=20,
    current_page=1,
    has_more=True,
    filters={"start_date": "2024-01-01"}
)
# Returns: {"cursor": "...", "has_more": True, "limit": 20, "returned": 20}
```

#### Time Utils (`time_utils.py`)

Module for time/date handling:

```python
from .time_utils import parse_time_range, get_range_description

# Parse period strings
start, end = parse_time_range("30d")        # Last 30 days
start, end = parse_time_range("this-week") # This week
start, end = parse_time_range("2024-01-01:2024-01-31")  # Absolute range

# Get human-readable descriptions
description = get_range_description("30d")  # "Last 30 days"
```

## Available Tools

The server provides **22 tools** organized into 8 categories:

- **Activities (3):** query_activities, get_activity_details, get_activity_social
- **Analysis (2):** compare_activities, find_similar_activities
- **Health & Wellness (4):** query_health_summary, query_sleep_data, query_heart_rate_data, query_activity_metrics
- **Training (3):** analyze_training_period, get_performance_metrics, get_training_effect
- **User Profile (1):** get_user_profile
- **Challenges & Goals (2):** query_goals_and_records, query_challenges
- **Devices & Gear (2):** query_devices, query_gear
- **Weight Management (2):** query_weight_data, manage_weight_data
- **Other (3):** manage_workouts, log_health_data, query_womens_health

See README.md for detailed tool descriptions and parameters.

## Tool Organization & Design Patterns

### Tool Design Philosophy

Use-case-focused tools with unified query patterns:

```python
# Single tool handles multiple query patterns
@mcp.tool()
async def query_activities(
    activity_id: str | None = None,  # Specific activity
    start_date: str | None = None,   # Range query
    end_date: str | None = None,
    date: str | None = None,         # Single date
    cursor: str | None = None,       # Pagination cursor
    limit: int | None = None,        # Page size
    activity_type: str | None = None # Filter
) -> str:
    """Query activities with flexible parameters and pagination."""
    # Implementation handles all patterns
```

This approach provides better LLM integration by offering flexible parameters
that adapt to different query needs within a single tool interface.

### Pagination Pattern

Tools that return large datasets support cursor-based pagination to prevent MCP size limits (1MB responses, 100k character truncation):

```python
# Query first page
response = await query_activities(start_date="2024-01-01", end_date="2024-12-31", limit=20)

# Check if more data available
data = json.loads(response)
if data.get("pagination", {}).get("has_more"):
    cursor = data["pagination"]["cursor"]
    # Fetch next page
    next_response = await query_activities(cursor=cursor)
```

**Pagination Response Structure:**
```json
{
  "data": {
    "activities": [...],
    "count": 20
  },
  "pagination": {
    "cursor": "eyJwYWdlIjoyLCJmaWx0ZXJzIjp7InN0YXJ0X2RhdGUiOiIyMDI0LTAxLTAxIn19",
    "has_more": true,
    "limit": 20,
    "returned": 20
  },
  "metadata": {...}
}
```

**Key Features:**
- **Stateless cursors**: Encode page number + filters (Base64 JSON)
- **Auto-detection**: Fetch limit+1 items to detect more pages
- **Preserved filters**: Cursor maintains query parameters
- **Compact JSON**: No indentation to minimize response size
- **Default limits**: 10 for activities, 7 for health data

**Tools with Pagination:**
- `query_activities`: Activities by date range or general queries (limit: 1-50, default 10)
- `query_health_summary`: Health data for date ranges (limit: 1-30, default 7)

### Structured Response Pattern

All tools should return structured JSON using `ResponseBuilder`:

```python
@mcp.tool()
async def analyze_training_period(period: str = "30d") -> str:
    """Analyze training over a period."""
    client = _get_client()

    # Parse time range
    start_date, end_date = parse_time_range(period)

    # Fetch data
    activities = client.safe_call("get_activities_by_date", start_date, end_date)

    # Calculate metrics
    data = {
        "period": {...},
        "summary": {...},
        "by_activity_type": [...],
        "trends": {...}
    }

    # Generate insights
    analysis = {
        "insights": [
            "High training volume: 15 activities in 31 days",
            "Training focused on running"
        ]
    }

    # Build response
    return ResponseBuilder.build_response(
        data=data,
        analysis=analysis,
        metadata={"period": get_range_description(period)}
    )
```

### Tool Implementation Guidelines

1. **Use type hints:** All parameters and return types should be annotated
2. **Provide docstrings:** Clear descriptions for LLM understanding
3. **Use `_get_client()` pattern:** Tools use a module-level global client instance
4. **Handle errors gracefully:** Use `ResponseBuilder.build_error_response()`
5. **Return structured JSON:** Use `ResponseBuilder.build_response()`
6. **Support unit preferences:** Accept `unit` parameter ("metric" or "imperial")
7. **Provide formatted output:** Include both raw values and human-readable formatting

## Testing Strategy

### Test Organization

```
tests/
├── conftest.py            # Pytest fixtures and configuration
├── test_formatters.py     # Formatter utility tests
├── test_response_builder.py  # Response builder tests
├── test_time_utils.py     # Time utility tests
└── test_tools/            # Tool-specific tests
    ├── test_activities.py
    ├── test_health_wellness.py
    └── ...
```

### Mocking Garmin API

Use `pytest-mock` to mock API responses:

```python
import pytest
from garmin_connect_mcp.client import GarminConnectClient

@pytest.fixture
def mock_client(mocker):
    """Mock Garmin Connect client."""
    client = mocker.MagicMock(spec=GarminConnectClient)
    # Mock specific methods
    client.get_activities.return_value = [...]
    return client

async def test_query_activities(mock_client):
    """Test activity querying."""
    result = await query_activities(start_date="2024-01-01", context=None)
    # Assertions
```

### Test Fixtures

Common fixtures in `conftest.py`:

- `mock_client`: Mocked Garmin Connect client
- `sample_activity`: Sample activity data
- `sample_sleep_data`: Sample sleep data
- `freeze_time`: Freeze time for consistent date-based tests

### Coverage Requirements

- Aim for >80% code coverage
- All new tools must have unit tests
- Test both success and error paths
- Test edge cases (empty data, null values, etc.)

## OAuth Flow

### Authentication Process

1. **Initial Authentication:**
   - User provides email/password via `.env` file
   - Server calls `garminconnect` library to authenticate
   - MFA prompt if enabled (interactive stdin)
   - OAuth tokens received and stored

2. **Token Storage:**
   - Tokens saved to `~/.garminconnect/`
   - Includes OAuth1 and OAuth2 tokens
   - Session cookies preserved

3. **Token Refresh:**
   - Tokens automatically refreshed by `garminconnect` library
   - Refresh happens transparently on API calls
   - No user intervention required

4. **Session Management:**
   - Server maintains session per request via MCP context
   - Context lifecycle managed by FastMCP
   - Client cached in context for request duration

### Security Considerations

- Credentials stored in `.env` (not committed to git)
- Tokens stored in user home directory
- No plaintext password transmission after initial auth
- OAuth tokens have expiration and refresh cycle

## MCP Integration

### Tools

Tools are the primary interface for LLM queries:

```python
@mcp.tool()
async def tool_name(
    param1: str,
    param2: int | None = None,
) -> str:
    """Tool description for LLM understanding."""
    client = _get_client()
    # Fetch data from Garmin API
    data = client.safe_call("garmin_api_method", param1)
    # Return structured response
    return ResponseBuilder.build_response(data=data, analysis=...)
```

### Resources

Resources provide ongoing context to the LLM:

```python
@mcp.resource("garmin://athlete/profile")
async def athlete_profile_resource() -> str:
    """Provide athlete profile for context."""
    # Call existing tool function to get profile data
    return await get_user_profile(
        include_stats=True,
        include_prs=True,
        include_devices=True,
    )
```

Resources are automatically fetched by context-aware MCP clients. Resources typically call existing tool functions to provide consistent data structure.

### Prompts

Prompts are pre-built query templates:

```python
from textwrap import dedent

@mcp.prompt()
async def analyze_recent_training(period: str = "30d") -> str:
    """Analyze training for a period."""
    return dedent(f"""
        Analyze my Garmin training over the past {period}.

        Focus on:
        1. Total volume (distance, time, elevation)
        2. Training distribution by activity type
        3. Weekly trends and patterns
        4. Performance metrics (VO2 max, training load)

        Use the analyze-training-period tool with period="{period}".
    """).strip()
```

Prompts help users execute common queries without crafting prompts manually.

## Common Development Tasks

### Adding a New Tool

1. Identify the use case and parameters
2. Implement in appropriate `tools/*.py` file
3. Use `@mcp.tool()` decorator (FastMCP will auto-register when imported in server.py)
4. Use `_get_client()` pattern for API access
5. Use `ResponseBuilder` for structured responses
6. Add comprehensive docstring with parameter descriptions
7. Write unit tests
8. Register tool in `server.py` with `mcp.tool()(your_function)`
9. Update README.md with tool description

### Adding a Resource

1. Design resource URI (e.g., `garmin://resource/name`)
2. Implement using `@mcp.resource()` decorator
3. Return structured JSON via `ResponseBuilder`
4. Ensure data is suitable for ongoing context
5. Test resource fetching
6. Document in README.md

### Adding a Prompt

1. Identify common query pattern
2. Design prompt template with parameters
3. Implement using `@mcp.prompt()` decorator
4. Reference appropriate tools in prompt text
5. Test prompt generation with various parameters
6. Document in README.md

## Debugging Tips

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Test with MCP Inspector

The MCP Inspector provides a web UI for testing tools:

```bash
npx @modelcontextprotocol/inspector uv run garmin-connect-mcp
```

Access at http://localhost:5173

### Common Issues

**Authentication Failures:**
- Check `.env` file exists and has correct credentials
- Delete `~/.garminconnect/` to clear cached tokens
- Re-run `uv run garmin-connect-mcp-auth`

**MFA Required:**
- Server prompts for MFA code on stdin
- Ensure running in interactive terminal
- Docker requires `-it` flags for interactive mode

**API Rate Limiting:**
- Garmin Connect has rate limits
- Use caching layer in `cache.py`
- Add delays between rapid API calls

## Performance Considerations

- **Caching:** Use `cache.py` to cache API responses
- **Batch Requests:** Consolidate multiple API calls when possible
- **Lazy Loading:** Only fetch detailed data when requested
- **Response Size:** Limit large arrays in responses (use summary + detail pattern)

## Contributing Guidelines

1. Follow existing code style (enforced by ruff)
2. Add type hints to all functions
3. Write comprehensive docstrings
4. Add unit tests for new functionality
5. Update documentation
6. Ensure all tests pass: `uv run pytest`
7. Run linting: `uv run ruff check .`
8. Run type checking: `uv run pyright`
