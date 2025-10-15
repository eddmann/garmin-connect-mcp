"""Type definitions for Garmin Connect API data structures."""

from typing import Literal, TypedDict

# Unit system type for consistent formatting across tools
UnitSystem = Literal["metric", "imperial"]


class SleepScoreComponent(TypedDict, total=False):
    """Individual sleep score component."""

    value: int
    qualifierKey: str


class SleepScores(TypedDict, total=False):
    """Sleep quality scores."""

    overall: SleepScoreComponent
    quality: SleepScoreComponent
    duration: SleepScoreComponent
    recovery: SleepScoreComponent


class DailySleepDTO(TypedDict, total=False):
    """Daily sleep data transfer object."""

    sleepStartTimestampLocal: int | str
    sleepEndTimestampLocal: int | str
    sleepTimeSeconds: int
    deepSleepSeconds: int
    lightSleepSeconds: int
    remSleepSeconds: int
    awakeSleepSeconds: int
    sleepScores: SleepScores


class SleepData(TypedDict, total=False):
    """Sleep data structure from Garmin API."""

    dailySleepDTO: DailySleepDTO
    restlessMomentsCount: int
    avgOvernightHrv: float
    restingHeartRate: int
    bodyBatteryChange: int
    sleepMovement: list[list[int | float]]
    sleepHeartRate: list[list[int | float]]
    wellnessEpochRespirationDataDTOList: list[dict[str, int | float]]


class StressData(TypedDict, total=False):
    """Stress data structure from Garmin API."""

    calendarDate: str
    startTimestampLocal: str
    endTimestampLocal: str
    avgStressLevel: int
    maxStressLevel: int
    stressValuesArray: list[list[int | float]]
    bodyBatteryValuesArray: list[list[int | float]]


class HeartRateData(TypedDict, total=False):
    """Heart rate data structure from Garmin API (dictionary format)."""

    restingHeartRate: int
    averageHeartRate: int
    minHeartRate: int
    maxHeartRate: int
    heartRateValues: list[list[int | float]]


# Heart rate can also be a list of timestamp/value pairs
HeartRateListData = list[list[int | float | None]]


class StepsData(TypedDict, total=False):
    """Steps/activity data structure from Garmin API."""

    totalSteps: int
    dailyStepGoal: int
    totalDistanceMeters: float
    activeKilocalories: float
    stepsArray: list[dict[str, int | float | str]]


class StepsListItem(TypedDict, total=False):
    """Individual step data item in list format."""

    steps: int
    startGMT: str
    endGMT: str


# Steps can also be a list of time period data
StepsListData = list[StepsListItem]


class StepsRangeItem(TypedDict, total=False):
    """Steps data for a single day in a range query."""

    calendarDate: str
    totalSteps: int
    stepGoal: int
    totalDistance: float


# JSON serializable types
JSONSerializable = (
    dict[str, "JSONSerializable"] | list["JSONSerializable"] | str | int | float | bool | None
)
