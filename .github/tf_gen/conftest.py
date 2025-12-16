from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture
def testdata_dir() -> Path:
    return Path(__file__).parent / "testdata"


@pytest.fixture
def backup_schedule_schema(testdata_dir: Path) -> dict:
    return json.loads(
        (testdata_dir / "mongodbatlas_cloud_backup_schedule.json").read_text()
    )


@pytest.fixture
def vpc_endpoint_schema(testdata_dir: Path) -> dict:
    return json.loads((testdata_dir / "vpc_endpoint.json").read_text())


@pytest.fixture
def advanced_cluster_schema(testdata_dir: Path) -> dict:
    return json.loads((testdata_dir / "mongodbatlas_advanced_cluster.json").read_text())


@pytest.fixture
def project_schema(testdata_dir: Path) -> dict:
    return json.loads((testdata_dir / "project.json").read_text())


@pytest.fixture
def database_user_schema(testdata_dir: Path) -> dict:
    return json.loads((testdata_dir / "mongodbatlas_database_user.json").read_text())


@pytest.fixture
def advanced_cluster_v2_schema(testdata_dir: Path) -> dict:
    return json.loads(
        (testdata_dir / "mongodbatlas_advanced_clusterv2.json").read_text()
    )
