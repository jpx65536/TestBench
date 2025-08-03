import requests

def test_health(wait_for_server, base_url):
    r = requests.get(f"{base_url}/testplatform/healthz/")
    assert r.status_code == 200