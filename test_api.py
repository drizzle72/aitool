import requests
import json

url = "https://www.runninghub.cn/task/openapi/create"
headers = {
    "User-Agent": "Apifox/1.0.0 (https://apifox.com)",
    "Content-Type": "application/json",
    "Accept": "*/*",
    "Host": "www.runninghub.cn"
}
data = {
    "workflowId": 1894278785376890882,
    "apiKey": "a2b6d581ad3c4544bbef2e593d47bbd4",
    "nodeInfoList": [
        {
            "nodeId": 6,
            "fieldName": "text",
            "fieldValue": "This FOUR-PANEL picture shows a young woman taking a walk by the seaside; [TOP-LEFT] She stood by the seaside, smiling and looking at the camera. [TOP-RIGHT] She made a gesture of empathy and looked at the camera. [BOTTOM-LEFT] She crossed her hands and looked at the camera. [BOTTOM-RIGHT] She put on her glasses and stood sideways, looking at the camera."
        }
    ]
}

print("Request data:", json.dumps(data, indent=2))
response = requests.post(url, headers=headers, json=data)
print(f"\nStatus Code: {response.status_code}")
print(f"Response: {response.text}") 