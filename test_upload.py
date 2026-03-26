import requests
import time

url = 'http://localhost:8000/upload'
files = {'file': open('data/uploads/PyPhi__A_toolbox_for_integrated_information.pdf', 'rb')}
r = requests.post(url, files=files)
print(r.json())

# Wait a bit for processing
time.sleep(10)

url = 'http://localhost:8000/graph'
r2 = requests.get(url)
print("Graph nodes:", len(r2.json().get('nodes', [])))
