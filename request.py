import requests
url = f"http://localhost:8888/tool-use-agent/search"
payload = {
    "query": "Hello",
    "image_description": ""
}
response = requests.post(url, json=payload)
response.raise_for_status()
response = response.json()
print(response["text"].replace("http://minio", "http://localhost"))