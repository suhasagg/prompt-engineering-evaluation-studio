from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app)
def test_experiment():
 r=c.post('/api/v1/experiments',json={"prompts":[{"name":"p1","template":"Return JSON. INPUT: {{input}}"}],"dataset":[{"input":"great product"}],"models":["mock-strict"],"output_mode":"json","json_required_keys":["sentiment","answer"]})
 assert r.status_code==200
 assert r.json()["summary"][0]["json_valid_rate"]==1.0
