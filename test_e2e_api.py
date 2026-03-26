import requests, time, sys
url = 'http://localhost:8000/upload'
try:
    files = {'file': open('grobid/grobid-service/src/test/resources/sample2/sample.pdf', 'rb')}
    r = requests.post(url, files=files)
    print("Upload status:", r.status_code, r.text)
except Exception as e:
    print("Failed to fetch /upload:", e)
    sys.exit(1)

for i in range(30):
    time.sleep(5)
    r2 = requests.get('http://localhost:8000/graph')
    data = r2.json()
    nodes = data.get('nodes', [])
    print(f"Graph nodes: {len(nodes)}")
    if len(nodes) > 0:
        print("SUCCESS! Graph contains nodes.")
        sys.exit(0)
print("Timeout. Graph still empty.")
sys.exit(1)
