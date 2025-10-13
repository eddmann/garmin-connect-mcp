"""Pytest configuration and shared fixtures."""

import pytest

from garmin_connect_mcp.types import HeartRateData, SleepData, StepsData, StressData


@pytest.fixture
def sample_sleep_data() -> SleepData:
    """Sample sleep data matching Garmin API response structure."""
    return {
        "dailySleepDTO": {
            "sleepStartTimestampLocal": 1705276800000,  # 2024-01-15 00:00:00
            "sleepEndTimestampLocal": 1705305600000,  # 2024-01-15 08:00:00
            "sleepTimeSeconds": 28800,  # 8 hours
            "deepSleepSeconds": 7200,  # 2 hours
            "lightSleepSeconds": 18000,  # 5 hours
            "remSleepSeconds": 3600,  # 1 hour
            "awakeSleepSeconds": 600,  # 10 minutes
            "sleepScores": {
                "overall": {"value": 85, "qualifierKey": "GOOD"},
                "quality": {"value": 82, "qualifierKey": "GOOD"},
                "duration": {"value": 88, "qualifierKey": "GOOD"},
                "recovery": {"value": 84, "qualifierKey": "GOOD"},
            },
        },
        "restlessMomentsCount": 12,
        "avgOvernightHrv": 55.3,
        "restingHeartRate": 58,
        "bodyBatteryChange": 42,
    }


@pytest.fixture
def sample_stress_data() -> StressData:
    """Sample stress data matching Garmin API response structure."""
    return {
        "calendarDate": "2024-01-15",
        "startTimestampLocal": "2024-01-15T00:00:00",
        "endTimestampLocal": "2024-01-15T23:59:59",
        "avgStressLevel": 35,
        "maxStressLevel": 72,
        "stressValuesArray": [[1705276800, 30], [1705280400, 35], [1705284000, 40]],
        "bodyBatteryValuesArray": [[1705276800, 75], [1705280400, 70], [1705284000, 65]],
    }


@pytest.fixture
def sample_heart_rate_data() -> HeartRateData:
    """Sample heart rate data (dictionary format)."""
    return {
        "restingHeartRate": 58,
        "averageHeartRate": 75,
        "minHeartRate": 55,
        "maxHeartRate": 145,
        "heartRateValues": [[1705276800, 60], [1705280400, 65], [1705284000, 70]],
    }


@pytest.fixture
def sample_heart_rate_list():
    """Sample heart rate data (list format)."""
    return [
        [1705276800, 60],
        [1705280400, 65],
        [1705284000, 70],
        [1705287600, 72],
        [1705291200, 68],
    ]


@pytest.fixture
def sample_steps_data() -> StepsData:
    """Sample steps data matching Garmin API response structure."""
    return {
        "totalSteps": 10543,
        "dailyStepGoal": 10000,
        "totalDistanceMeters": 7850.5,
        "activeKilocalories": 425.3,
        "stepsArray": [
            {"steps": 1200, "startGMT": "2024-01-15T08:00:00", "endGMT": "2024-01-15T09:00:00"},
            {"steps": 2340, "startGMT": "2024-01-15T09:00:00", "endGMT": "2024-01-15T10:00:00"},
            {"steps": 1800, "startGMT": "2024-01-15T10:00:00", "endGMT": "2024-01-15T11:00:00"},
        ],
    }
