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

# thêm 1 agent thì phải sửa gồm: 
# agent_card
# sub_agent thêm 1 src, thêm trong get_agent_executor của main
# sửa prompts
# host_agent phải sửa url trong .env và prompt, thêm trong hàm 
# docker-compose