import asyncio
import httpx
import firebase_admin
from firebase_admin import credentials, auth
import json
import os

API_BASE = "http://127.0.0.1:8000/api/v1"
IMAGE_PATH = r"C:\Users\aksha\.gemini\antigravity-ide\brain\897d7a87-e94a-4b79-8673-6e6de9a2a186\dummy_prescription_1783488350137.png"

async def main():
    email = "ocr_test_doc@example.com"
    phone = "+19998889999"

    async with httpx.AsyncClient(timeout=30.0) as client:
        print("1. Sending OTP...")
        await client.post(f"{API_BASE}/auth/otp/send", json={"email": email})

        print("2. Verifying OTP (getting backend token)...")
        resp = await client.post(f"{API_BASE}/auth/otp/verify", json={"email": email, "otp": "123456"})
        if resp.status_code != 200:
            print("OTP Verify Failed:", resp.text)
            return
            
        backend_token = resp.json()["data"]["access_token"]
        role = resp.json()["data"]["role"]
        
        doctor_token = backend_token
        headers = {"Authorization": f"Bearer {doctor_token}"}
        
        if role == "unregistered":
            print("3. Registering Doctor...")
            resp = await client.post(f"{API_BASE}/doctors/register", json={
                "name": "Dr. AI Tester",
                "phone": phone,
                "specialization": "AI Med",
                "license_number": "MED-AI-9999",
                "hospital_or_clinic": "Gemini Hospital"
            }, headers=headers)
            
            print("4. Getting Doctor Token...")
            await client.post(f"{API_BASE}/auth/otp/send", json={"email": email})
            resp = await client.post(f"{API_BASE}/auth/otp/verify", json={"email": email, "otp": "123456"})
            doctor_token = resp.json()["data"]["access_token"]
            headers = {"Authorization": f"Bearer {doctor_token}"}

        
        print("5. Uploading Image to OCR (This will call Gemini Vision!)...")
        with open(IMAGE_PATH, "rb") as f:
            files = {"file": ("dummy_prescription.png", f, "image/png")}
            resp = await client.post(f"{API_BASE}/ocr/upload", files=files, headers=headers)
            
        print("Upload Response:", resp.status_code, resp.text)
        if resp.status_code != 201:
            return
            
        source_id = resp.json()["data"]["id"]
        
        print("\n6. Fetching AI Extraction Draft...")
        resp = await client.get(f"{API_BASE}/ocr/{source_id}", headers=headers)
        print("Draft JSON:")
        print(json.dumps(resp.json()["data"]["ai_extracted_json"], indent=2))
        
        print("\n7. Confirming Extraction...")
        resp = await client.post(f"{API_BASE}/ocr/{source_id}/confirm", headers=headers)
        print("Confirm Response:", resp.status_code, resp.text)
        
        print("\n8. Listing Doctor's Prescriptions to verify...")
        resp = await client.get(f"{API_BASE}/prescriptions/mine", headers=headers)
        print("Prescriptions:")
        print(json.dumps(resp.json()["data"], indent=2))

if __name__ == "__main__":
    asyncio.run(main())
