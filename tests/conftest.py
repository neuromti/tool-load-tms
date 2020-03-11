import pytest
from pathlib import Path


@pytest.fixture(scope="session")
def matfile():
    yield Path(__file__).parent / "map_contralesional.mat"
