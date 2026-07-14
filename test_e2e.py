import asyncio
import httpx
import firebase_admin
from firebase_admin import credentials, auth
from datetime import datetime, timedelta
import json
import os

API_BASE = "http://127.0.0.1:8000/api/v1"
IMAGE_PATH = r"C:\Users\aksha\.gemini\antigravity-ide\brain\897d7a87-e94a-4b79-8673-6e6de9a2a186\dummy_prescription_1783488350137.png"

# We use the same service account file
cred_path = r'c:\Users\aksha\Desktop\MediQR\mediqr-917f9-firebase-adminsdk-fbsvc-ab41a12577.json'
if not firebase_admin._apps:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)

async def register_and_get_token(client, email, phone, role, register_data):
    # 1. Send OTP
    send_resp = await client.post(f"{API_BASE}/auth/otp/send", json={"email": email})
    if send_resp.status_code != 200:
        print(f"Send OTP failed: {send_resp.text}")

    # 2. Verify OTP
    resp = await client.post(f"{API_BASE}/auth/otp/verify", json={"email": email, "otp": "123456"})
    if resp.status_code != 200:
        print(f"Verify OTP failed: {resp.text}")
    
    data = resp.json().get("data", {})
    if data.get("role") == "unregistered":
        endpoint = "/doctors/register" if role == "doctor" else "/patients/register"
        headers = {"Authorization": f"Bearer {data.get('access_token', '')}"}
        
        register_data["phone"] = phone
        reg_resp = await client.post(f"{API_BASE}{endpoint}", json=register_data, headers=headers)
        if reg_resp.status_code not in (200, 201):
            print(f"Failed to register {role}: {reg_resp.text}")
            
        await client.post(f"{API_BASE}/auth/otp/send", json={"email": email})
        resp = await client.post(f"{API_BASE}/auth/otp/verify", json={"email": email, "otp": "123456"})
        
    data = resp.json()["data"]
    print(f"Got token for {role}. Role in token data: {data.get('role')}")
    return data["access_token"]

async def main():
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("=== 1. Setup & Auth ===")
        doc1_token = await register_and_get_token(client, 'e2e_doc1@example.com', '+15551111111', 'doctor', {
            "name": "Dr. E2E One", "specialization": "General", "license_number": "DOC-1", "hospital_or_clinic": "Clinic 1"
        })
        doc2_token = await register_and_get_token(client, 'e2e_doc2@example.com', '+15552222222', 'doctor', {
            "name": "Dr. E2E Two", "specialization": "Specialist", "license_number": "DOC-2", "hospital_or_clinic": "Clinic 2"
        })
        pat1_token = await register_and_get_token(client, 'e2e_pat1@example.com', '+15553333333', 'patient', {
            "name": "Patient One", "dob": "1990-01-01"
        })
        
        doc1_headers = {"Authorization": f"Bearer {doc1_token}"}
        doc2_headers = {"Authorization": f"Bearer {doc2_token}"}
        pat1_headers = {"Authorization": f"Bearer {pat1_token}"}
        
        print("=== 2. Doctor 1 Creates Prescription ===")
        # We will just create it manually to bypass Gemini 503 issues
        manual_prescription_data = {
            "till_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "notes": "E2E Test Note",
            "medicines": [
                {
                    "name": "Amoxicillin",
                    "dosage": "500mg",
                    "instructions": "Take 1 tablet",
                    "times_per_day": ["08:00:00", "20:00:00"]
                }
            ]
        }
        resp = await client.post(f"{API_BASE}/prescriptions", json=manual_prescription_data, headers=doc1_headers)
        if resp.status_code != 201:
            print("Create Prescription Failed:", resp.text)
            
        prescription_id = resp.json()["data"]["id"]
        print(f"Prescription created! ID: {prescription_id}")
        
        print("=== 4. Doctor 1 Generates Prescription QR ===")
        qr_resp = await client.post(f"{API_BASE}/qr/prescription/{prescription_id}", headers=doc1_headers)
        prescription_token = qr_resp.json()["data"]["token"]
        
        print("=== 5. Patient 1 Claims Prescription ===")
        claim_resp = await client.post(f"{API_BASE}/qr/prescription/claim", json={"token": prescription_token}, headers=pat1_headers)
        if claim_resp.status_code != 200:
            print("Failed to claim prescription:", claim_resp.text)
        print("Claimed!", claim_resp.json().get("data"))
        
        print("=== 6. Patient 1 Checks Doses ===")
        doses_resp = await client.get(f"{API_BASE}/doses?prescription_id={prescription_id}", headers=pat1_headers)
        doses = doses_resp.json()["data"]
        print(f"Found {len(doses)} scheduled doses.")
        if doses:
            first_dose_id = doses[0]["id"]
            mark_resp = await client.post(f"{API_BASE}/doses/{first_dose_id}/mark-taken", headers=pat1_headers)
            print(f"Marked dose {first_dose_id} as taken! Status: {mark_resp.json()['data']['marked_status']}")
            
        print("=== 7. Patient 1 Generates History QR ===")
        hist_qr_resp = await client.post(f"{API_BASE}/qr/history", json={"scope": "all"}, headers=pat1_headers)
        hist_token = hist_qr_resp.json()["data"]["token"]
        
        print("=== 8. Doctor 2 Scans History QR ===")
        scan_resp = await client.post(f"{API_BASE}/qr/history/claim", json={"token": hist_token}, headers=doc2_headers)
        shared_history = scan_resp.json()["data"]["prescriptions"]
        print(f"Doctor 2 sees {len(shared_history)} prescriptions in history!")
        assert len(shared_history) > 0, "Doctor 2 should see the prescription!"
        
        print("=== 9. Patient 1 Views Access Logs ===")
        logs_resp = await client.get(f"{API_BASE}/qr/history/access-logs", headers=pat1_headers)
        logs = logs_resp.json()["data"]
        print(f"Access Logs: {json.dumps(logs, indent=2)}")
        assert len(logs) > 0, "Access log should exist!"
        
        print("\n[SUCCESS] End-to-End Test Passed!")

if __name__ == "__main__":
    asyncio.run(main())
