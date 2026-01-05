from openCHA.tasks.custom.awakenings_detection import AwakeningsDetection
from openCHA.tasks.custom.eda_feature_extraction import EDAFeatureExtraction
from openCHA.tasks.custom.sleep_disorders_intervals import SleepDisordersIntervals
from openCHA.tasks.custom.sleep_quality_from_eda import SleepQualityFromEDA

__all__ = [
    "AwakeningsDetection",
    "SleepDisordersIntervals",
    "EDAFeatureExtraction",
    "SleepQualityFromEDA",
]