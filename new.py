import requests

data = {
    "doc_id": "resume1",
    "text": "This is a sample resume. It contains information about skills, education, and experience."
}

res = requests.post("http://127.0.0.1:8000/ingest", json=data)
print(res.status_code)
print(res.text)
if res.status_code == 200:
    print(res.json())
