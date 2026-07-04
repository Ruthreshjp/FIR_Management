import json
import os
import requests

payload = {
    "complainant_name": "Test User",
    "complainant_address": "123 Test St",
    "complainant_city": "Test City",
    "complainant_phone": "1234567890",
    "incident_location": "Test Location",
    "incident_date": "2026-07-03",
    "incident_time": "12:00",
    "complaint_text": "On the night of 1st July 2026, Ramesh Babu along with two unidentified persons came to our house and called my brother Vikram outside. Ramesh Babu attacked him with a sharp knife and stabbed him multiple times in the chest. The two persons held Vikram from behind. Vikram died at the hospital. Ramesh Babu and accomplices fled in a white Innova car."
}

with requests.post("http://127.0.0.1:5000/api/firs/generate", json=payload, stream=True) as r:
    for line in r.iter_lines():
        if line:
            print(line.decode('utf-8'))
