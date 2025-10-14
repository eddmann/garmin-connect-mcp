# Garmin Connect MCP Server

A Model Context Protocol (MCP) server for Garmin Connect integration. Access your activities, health data, training metrics, and more through Claude and other LLMs with intelligent analysis and insights.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-1.3.1-green.svg)](https://modelcontextprotocol.io)

## Overview

This MCP server provides **21 tools** with intelligent analysis, **3 MCP resources** for ongoing context, and **6 MCP prompts** for common queries. Tools are organized by use-case, providing better LLM integration and richer insights.

**Key Features:**
- 🎯 **Use-case focused tools** - Unified interfaces for related operations
- 📊 **Structured responses** - Consistent JSON with data, analysis, and metadata
- 🔍 **Rich analysis** - Automatic insights and pattern detection
- 📈 **Training analysis** - Comprehensive training period analysis
- 🔄 **Activity comparison** - Side-by-side activity comparisons
- 🎲 **Similarity search** - Find similar activities
- 🌍 **Unit support** - Both metric and imperial units
- 📚 **MCP resources** - Ongoing context for athlete profile, training readiness, health
- ⚡ **MCP prompts** - Pre-built templates for common queries

## Prerequisites

- Python 3.11+ and [uv](https://github.com/astral-sh/uv), OR
- Docker

## Installation & Setup

### How Authentication Works

1. **First Run**: Server authenticates with your Garmin Connect credentials
2. **MFA Support**: If enabled, prompts for your MFA code (interactive stdin)
3. **Token Storage**: OAuth tokens saved to `~/.garminconnect/` and automatically refreshed
4. **UV**: Tokens persist across runs
5. **Docker**: Tokens are ephemeral (container authenticates on each restart)

### Option 1: Using UV

```bash
# Install dependencies
cd my-garmin-connect-mcp
uv sync
```

Then configure credentials using one of these methods:

#### Interactive Setup

```bash
uv run garmin-connect-mcp-auth
```

This will prompt for your credentials (and MFA code if needed) and save them to `.env`.

#### Manual Setup

Create a `.env` file manually:

```bash
GARMIN_EMAIL=your-email@example.com
GARMIN_PASSWORD=your-password
```

### Option 2: Using Docker

```bash
# Pull the image
docker pull ghcr.io/eddmann/garmin-connect-mcp:latest
```

Then configure credentials using one of these methods:

#### Interactive Setup

```bash
# Create the env file first (Docker will create it as a directory if it doesn't exist)
touch garmin-connect-mcp.env

# Run the setup script
docker run -it --rm \
  -v "/ABSOLUTE/PATH/TO/garmin-connect-mcp.env:/app/.env" \
  --entrypoint= \
  ghcr.io/eddmann/garmin-connect-mcp:latest \
  python -m garmin_connect_mcp.scripts.setup_auth
```

This will prompt for your credentials and save them to `garmin-connect-mcp.env`.

#### Manual Setup

Create a `garmin-connect-mcp.env` file manually in your current directory:

```bash
GARMIN_EMAIL=your-email@example.com
GARMIN_PASSWORD=your-password
```

## Claude Desktop Configuration

Add to your configuration file:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

### Using UV

```json
{
  "mcpServers": {
    "garmin-connect": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/ABSOLUTE/PATH/TO/my-garmin-connect-mcp",
        "garmin-connect-mcp"
      ]
    }
  }
}
```

### Using Docker

```json
{
  "mcpServers": {
    "garmin-connect": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v",
        "/ABSOLUTE/PATH/TO/garmin-connect-mcp.env:/app/.env",
        "ghcr.io/eddmann/garmin-connect-mcp:latest"
      ]
    }
  }
}
```

## Usage Examples

Ask Claude to interact with your Garmin data using natural language:

### Training Analysis

```
"Analyze my training over the last 30 days"
"Show me weekly trends for my running activities"
"How has my training volume changed this month?"
```

### Activity Comparison

```
"Compare my last 3 runs"
"Find activities similar to my morning run from yesterday"
"Show me how my pace has improved over recent rides"
```

### Health & Wellness

```
"How did I sleep last week?"
"What's my Body Battery level today?"
"Show me my stress levels and recovery status"
"Am I ready to train hard today?"
```

### Performance Metrics

```
"What's my VO2 max trend this month?"
"Show me my hill score progression"
"How's my HRV looking lately?"
```

## Available Tools (21)

### Activities (2 tools)

| Tool                     | Description                                                                  |
| ------------------------ | ---------------------------------------------------------------------------- |
| `query_activities`       | Unified activity queries (by ID, date range, specific date, pagination)     |
| `get_activity_details`   | Comprehensive activity details (splits, weather, HR zones, gear)             |

### Analysis (3 tools)

| Tool                      | Description                                     |
| ------------------------- | ----------------------------------------------- |
| `analyze_training_period` | Comprehensive training analysis with insights   |
| `compare_activities`      | Side-by-side activity comparison                |
| `find_similar_activities` | Find activities matching criteria               |

### Health & Wellness (4 tools)

| Tool                      | Description                                            |
| ------------------------- | ------------------------------------------------------ |
| `query_health_summary`    | Daily health snapshot (stats, training readiness, Body Battery) |
| `query_sleep_data`        | Sleep analysis with stages, scores, HRV                |
| `query_heart_rate_data`   | Heart rate data with resting HR                        |
| `query_activity_metrics`  | Activity metrics (steps, stress, respiration, SpO2, etc.) |

### Training (3 tools)

| Tool                      | Description                                            |
| ------------------------- | ------------------------------------------------------ |
| `analyze_training_period` | Training analysis for any period (see Analysis section) |
| `get_performance_metrics` | VO2 max, hill score, endurance, HRV, fitness age       |
| `get_training_effect`     | Training effect and progress summary                   |

### Challenges & Goals (2 tools)

| Tool                       | Description                                    |
| -------------------------- | ---------------------------------------------- |
| `query_goals_and_records`  | Goals, personal records, race predictions      |
| `query_challenges`         | Challenges and badges (by status and type)     |

### Devices & Gear (2 tools)

| Tool            | Description                                              |
| --------------- | -------------------------------------------------------- |
| `query_devices` | Device information (with settings, solar data, alarms)   |
| `query_gear`    | Gear and equipment (with defaults and usage stats)       |

### Weight Management (2 tools)

| Tool                  | Description                              |
| --------------------- | ---------------------------------------- |
| `query_weight_data`   | Weight data for date or range            |
| `manage_weight_data`  | Add or delete weight entries             |

### Other (3 tools)

| Tool                   | Description                                            |
| ---------------------- | ------------------------------------------------------ |
| `manage_workouts`      | Workout management (list, get, download, upload)       |
| `log_health_data`      | Log body composition, blood pressure, hydration        |
| `query_womens_health`  | Pregnancy and menstrual cycle data                     |
| `get_full_name`        | User profile name                                      |

## MCP Resources (3)

Resources provide ongoing context to context-aware MCP clients:

- `garmin://athlete/profile` - Athlete profile with stats and zones
- `garmin://training/readiness` - Current training readiness and Body Battery
- `garmin://health/today` - Today's health snapshot (steps, sleep, stress, HR)

## MCP Prompts (6)

Pre-built templates for common queries:

- `analyze_recent_training` - Analyze training over a period
- `sleep_quality_report` - Sleep quality analysis with recommendations
- `training_readiness_check` - Check if ready to train today
- `activity_deep_dive` - Comprehensive activity analysis
- `compare_recent_runs` - Compare recent runs for trends
- `health_summary` - Comprehensive health overview

## Response Format

All tools return structured JSON with:

```json
{
  "data": {
    // Primary data payload with rich formatting
    // Both raw values and human-readable formats
  },
  "analysis": {
    "insights": [
      // Automatic insights and patterns
    ]
  },
  "metadata": {
    "fetched_at": "2025-01-15T10:00:00Z",
    // Query parameters, unit system, etc.
  }
}
```

## Development

See [CLAUDE.md](CLAUDE.md) for comprehensive developer documentation including:

- Project architecture
- Development commands
- Tool design patterns
- Testing strategy
- Contributing guidelines

## License

MIT License - see [LICENSE](LICENSE) file for details

## Disclaimer

This project is not affiliated with, endorsed by, or sponsored by Garmin Ltd. or any of its affiliates. All product names, logos, and brands are property of their respective owners.
