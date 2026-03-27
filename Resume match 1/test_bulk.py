import requests
import os

url = "http://127.0.0.1:5000/match_bulk"
sample_dir = "sample_resumes"

# Prepare the data and files for the request
data = {
    "job_title": "Senior Python Backend Engineer",
    "job_skills": "Python, Flask, PostgreSQL, Supabase, AWS, Docker",
    "job_description": "We are looking for an experienced Backend Software Engineer to build scalable REST APIs and manage our database infrastructure. The ideal candidate has deep expertise in Python microservices, specifically using Flask. You will be responsible for designing database schemas in PostgreSQL (or Supabase) and deploying applications to AWS using Docker. We need someone who has experience handling high-traffic applications."
}

# Collect the files
files = []
for filename in os.listdir(sample_dir):
    if filename.endswith(".docx"):
        file_path = os.path.join(sample_dir, filename)
        # We must keep the file objects open while making the request
        files.append(("resumes", (filename, open(file_path, "rb"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")))

print(f"Sending request to {url} with {len(files)} files...")
response = requests.post(url, data=data, files=files)

print(f"Status Code: {response.status_code}")
if response.status_code == 200:
    print("Success! Data should now be saved in Supabase.")
    res = response.json()
    if 'ranked_candidates' in res:
        for c in res['ranked_candidates']:
            print(f"Rank {c['rank']}: {c['candidate_name']} - Score: {c['score']}%")
else:
    print("Error:", response.text)

# Close files
for f in files:
    f[1][1].close()
