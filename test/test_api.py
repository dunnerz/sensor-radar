import requests
import json
import time

with open("sample_request_range_1000.json") as f:
    payload = json.load(f)

# Use local server for testing progress
print("🚀 Starting coverage computation...")
res = requests.post("http://localhost:8000/", json=payload)

print("Status Code:", res.status_code)
print("Initial Response:", res.json())

if res.status_code == 200:
    job_data = res.json()
    job_id = job_data.get("job_id")
    
    if job_id:
        print(f"\n📈 Monitoring progress for job: {job_id}")
        
        # Monitor progress
        while True:
            progress_res = requests.get(f"http://localhost:8000/progress/{job_id}")
            
            if progress_res.status_code == 200:
                progress_data = progress_res.json()
                status = progress_data["status"]
                
                if status == "completed":
                    print(f"🎉 Completed! Found {progress_data['total_points']} coverage points")
                    break
                elif status == "error":
                    print(f"❌ Error: {progress_data.get('detail', 'Unknown error')}")
                    break
                else:
                    progress = progress_data.get("progress", 0)
                    processed = progress_data.get("processed_cells", 0)
                    total = progress_data.get("total_cells", 0)
                    print(f"⏳ Progress: {progress}% ({processed}/{total} cells)")
                    time.sleep(2)
            else:
                print(f"❌ Error checking progress: {progress_res.text}")
                break
else:
    print("❌ Error:", res.text)

