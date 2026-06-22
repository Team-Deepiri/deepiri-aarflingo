"""Catalog of open canine biomedical / wearable datasets used for training."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DatasetSource:
    id: str
    name: str
    modality: str
    url: str
    license: str
    notes: str


PUBLIC_DATASETS: tuple[DatasetSource, ...] = (
    DatasetSource(
        id="physiozoo-dog-ecg",
        name="PhysioZoo mammalian ECG (dogs)",
        modality="ecg",
        url="https://physionet.org/content/physiozoo/1.0.0/",
        license="Open Access (PhysioNet)",
        notes="Conscious dogs, 500 Hz surface ECG, R-peak annotations; HRV reference ranges.",
    ),
    DatasetSource(
        id="uwb-dvs",
        name="UWB radar dog vital signs (UWB-DVS)",
        modality="ecg",
        url="https://www.nature.com/articles/s41597-024-02947-4",
        license="CC BY 4.0",
        notes="Clinical BM7Vet Pro ECG reference + radar HR/BR for dogs.",
    ),
    DatasetSource(
        id="zenodo-dog-hrv-stress",
        name="Dog HRV during animal-assisted interventions",
        modality="ecg",
        url="https://zenodo.org/records/19383015",
        license="Zenodo record license",
        notes="Wearable ECG R-R intervals, cortisol, behavioral stress labels.",
    ),
    DatasetSource(
        id="mendeley-dog-posture-imu",
        name="Inertial sensor dog posture recognition",
        modality="imu",
        url="https://data.mendeley.com/datasets/mpph6bmn7g/1",
        license="CC BY 4.0",
        notes="42 dogs, neck/chest/back IMUs @ 100 Hz, standing/sitting/lying/walking/shake.",
    ),
    DatasetSource(
        id="mendeley-dog-behavior-imu",
        name="Movement sensor dog behavior classification",
        modality="imu",
        url="https://data.mendeley.com/datasets/vxhx934tbn/3",
        license="CC BY 4.0",
        notes="45 dogs, collar+harness 6-DoF IMU, walk/trot/sit/sniff/stand/gallop.",
    ),
)
