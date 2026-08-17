import urllib.request, json

token = "3W7NIy49Kh4KWf5j5ZNYM1JIMd8PixAiDXMb8eIoxvw"
project_id = "520adb72-b1f4-4021-8c4b-21ca81f8a901"

query = {"query": 'mutation { serviceCreate(input: {projectId: "%s", name: "Postgres", templateId: "postgres"}) { id name } }' % project_id}
req = urllib.request.Request("https://backboard.railway.com/graphql/v2")
req.add_header("Authorization", "Bearer %s" % token)
req.add_header("Content-Type", "application/json")
resp = urllib.request.urlopen(req, json.dumps(query).encode())
print(resp.read().decode())
