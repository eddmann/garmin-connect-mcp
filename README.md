# Garmin Connect MCP Server

A Model Context Protocol (MCP) server for Garmin Connect integration. Access your activities, health data, training metrics, and more through Claude and other LLMs.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-1.3.1-green.svg)](https://modelcontextprotocol.io)

## Overview

This MCP server provides 73 tools to interact with your Garmin Connect account, organized into 11 categories:

- Activities, Health & Wellness, Training, Challenges, Devices, Weight, Workouts, Gear, Data Management, Women's Health, and User Profile.

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

## Usage

Ask Claude to interact with your Garmin data using natural language:

### Activities

```
"Show me my activities from last week"
"What were the details of my last run?"
"Show me split data for activity 12345678"
"What was the weather during my morning ride?"
```

### Health & Wellness

```
"How did I sleep last night?"
"What's my Body Battery level today?"
"Show me my stress levels for yesterday"
"What's my resting heart rate this week?"
```

### Training

```
"What's my VO2 max progress this month?"
"Show me my hill score for the last 30 days"
"What are my current race predictions?"
"Show me my HRV data for today"
```

### Devices & Gear

```
"List all my Garmin devices"
"What's my primary training device?"
"Show me solar charging data for my watch"
```

### Challenges & Goals

```
"Show me my active challenges"
"What badges have I earned?"
"Show me my personal records"
```

### Data Management

```
"Add a weigh-in of 75kg"
"Record my blood pressure: 120/80"
"Add 500ml of water to my hydration log"
```

## Available Tools

### Activities (12 tools)

| Tool                           | Description                                        |
| ------------------------------ | -------------------------------------------------- |
| `get_activities`               | Get paginated list of activities                   |
| `get_activities_by_date`       | Get activities within a date range                 |
| `get_activities_fordate`       | Get activities for a specific date                 |
| `get_activity`                 | Get detailed activity information by ID            |
| `get_activity_splits`          | Get activity lap/split data                        |
| `get_activity_typed_splits`    | Get typed split data (e.g., kilometer splits)      |
| `get_activity_split_summaries` | Get summary of all activity splits                 |
| `get_activity_weather`         | Get weather conditions during an activity          |
| `get_activity_hr_in_timezones` | Get heart rate time in zones for an activity       |
| `get_activity_gear`            | Get gear used during an activity                   |
| `get_activity_exercise_sets`   | Get exercise sets for strength training activities |
| `get_last_activity`            | Get most recent activity                           |

### Health & Wellness (21 tools)

| Tool                      | Description                                   |
| ------------------------- | --------------------------------------------- |
| `get_stats`               | Get daily health statistics                   |
| `get_user_summary`        | Get comprehensive user health summary         |
| `get_body_composition`    | Get body composition metrics for a date range |
| `get_stats_and_body`      | Get combined stats and body data              |
| `get_steps_data`          | Get detailed step data for a specific date    |
| `get_daily_steps`         | Get daily steps for a date range              |
| `get_training_readiness`  | Get training readiness score                  |
| `get_body_battery`        | Get Body Battery™ energy levels               |
| `get_body_battery_events` | Get Body Battery charge/drain events          |
| `get_blood_pressure`      | Get blood pressure measurements               |
| `get_floors`              | Get floors climbed data                       |
| `get_training_status`     | Get current training status                   |
| `get_rhr_day`             | Get resting heart rate for a day              |
| `get_heart_rates`         | Get heart rate data for a date/range          |
| `get_hydration_data`      | Get hydration tracking data                   |
| `get_sleep_data`          | Get sleep analysis and sleep stages           |
| `get_stress_data`         | Get stress level measurements                 |
| `get_respiration_data`    | Get respiration rate data                     |
| `get_spo2_data`           | Get blood oxygen (SpO2) levels                |
| `get_all_day_stress`      | Get all-day stress tracking data              |
| `get_all_day_events`      | Get all-day health events                     |

### Training (7 tools)

| Tool                                 | Description                                     |
| ------------------------------------ | ----------------------------------------------- |
| `get_progress_summary_between_dates` | Get training progress summary for a date range  |
| `get_hill_score`                     | Get hill climbing performance score             |
| `get_endurance_score`                | Get endurance performance metrics               |
| `get_training_effect`                | Get training effect for a specific activity     |
| `get_max_metrics`                    | Get maximum performance metrics (VO2 max, etc.) |
| `get_hrv_data`                       | Get heart rate variability data                 |
| `get_fitnessage_data`                | Get fitness age calculation                     |

### Challenges (9 tools)

| Tool                                 | Description                            |
| ------------------------------------ | -------------------------------------- |
| `get_goals`                          | Get activity goals and targets         |
| `get_personal_record`                | Get personal records across activities |
| `get_earned_badges`                  | Get badges earned                      |
| `get_adhoc_challenges`               | Get ad-hoc challenges                  |
| `get_available_badge_challenges`     | Get available badge challenges         |
| `get_badge_challenges`               | Get all badge challenges               |
| `get_non_completed_badge_challenges` | Get incomplete badge challenges        |
| `get_race_predictions`               | Get race time predictions              |
| `get_inprogress_virtual_challenges`  | Get active virtual challenges          |

### Devices (6 tools)

| Tool                          | Description                                          |
| ----------------------------- | ---------------------------------------------------- |
| `get_devices`                 | List all registered Garmin devices                   |
| `get_device_last_used`        | Get most recently used device                        |
| `get_device_settings`         | Get device configuration settings                    |
| `get_primary_training_device` | Get primary training device                          |
| `get_device_solar_data`       | Get solar charging data (for solar-equipped devices) |
| `get_device_alarms`           | Get configured device alarms                         |

### Weight (4 tools)

| Tool                  | Description                        |
| --------------------- | ---------------------------------- |
| `get_weigh_ins`       | Get weigh-in data for a date range |
| `get_daily_weigh_ins` | Get weigh-ins for a specific date  |
| `delete_weigh_ins`    | Delete weigh-in entries            |
| `add_weigh_in`        | Add a new weigh-in record          |

### Workouts (4 tools)

| Tool                | Description                        |
| ------------------- | ---------------------------------- |
| `get_workouts`      | List all structured workouts       |
| `get_workout_by_id` | Get workout details by ID          |
| `download_workout`  | Get workout download information   |
| `upload_workout`    | Upload a workout to Garmin Connect |

### Gear (3 tools)

| Tool                | Description               |
| ------------------- | ------------------------- |
| `get_gear`          | List user gear/equipment  |
| `get_gear_defaults` | Get default gear settings |
| `get_gear_stats`    | Get gear usage statistics |

### Data Management (3 tools)

| Tool                   | Description                         |
| ---------------------- | ----------------------------------- |
| `add_body_composition` | Add a body composition entry        |
| `set_blood_pressure`   | Record a blood pressure measurement |
| `add_hydration_data`   | Add a hydration log entry           |

### Women's Health (3 tools)

| Tool                          | Description                                  |
| ----------------------------- | -------------------------------------------- |
| `get_pregnancy_summary`       | Get pregnancy tracking summary               |
| `get_menstrual_data_for_date` | Get menstrual cycle data for a specific date |
| `get_menstrual_calendar_data` | Get menstrual calendar data for a date range |

### User Profile (1 tool)

| Tool            | Description                                      |
| --------------- | ------------------------------------------------ |
| `get_full_name` | Get user's full name from Garmin Connect profile |

## License

MIT License - see [LICENSE](LICENSE) file for details

## Disclaimer

This project is not affiliated with, endorsed by, or sponsored by Garmin Ltd. or any of its affiliates. All product names, logos, and brands are property of their respective owners.
