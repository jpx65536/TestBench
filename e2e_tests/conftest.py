import pytest
import time
import requests
from orca.orca import start


@pytest.fixture(scope="session")
def base_url():
    return "http://localhost:8000"

@pytest.fixture(scope="session")
def wait_for_server(base_url):
    timeout = 30
    interval = 1
    start = time.time()
    while True:
        try:
            r = requests.get(f"{base_url}/testplatform/healthz/")
            if r.status_code == 200:
                return
        except requests.RequestException:
            pass
        if time.time() - start > timeout:
            pytest.exit(f"server did not become ready within {timeout}s")
        time.sleep(interval)