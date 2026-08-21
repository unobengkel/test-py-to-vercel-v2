from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
import base64
import time
import json
import uuid

app = FastAPI(title="KameraTamu Middleware Server")

# Izinkan akses CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# KONFIGURASI SUPABASE & AI SERVER
# ==========================================

SUPABASE_URL_1 = "https://wqqrjsjytlcvkkgziana.supabase.co"
SUPABASE_KEY_1 = "sb_publishable_nqnraHg2CUUot95hRWv5fA_ZuDozNyM"

SUPABASE_URL_2 = "https://tbgbulvofncfgntqrrya.supabase.co"
SUPABASE_KEY_2 = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRiZ2J1bHZvZm5jZmdudHFycnlhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzE5NDk1NjEsImV4cCI6MjA4NzUyNTU2MX0.EdlAomiUlbicGZRscxuW6fHNLqY-uA48jNcps_0ltE8"
TARGET_BUCKET = "photos"
TARGET_TABLE = "photos_data"

AI_SERVER_URL = "https://www.kameratamu.com/api/apply-filter"

HEADERS_SUPA_1 = {
    "apikey": SUPABASE_KEY_1,
    "Authorization": f"Bearer {SUPABASE_KEY_1}",
    "Content-Type": "application/json"
}

HEADERS_SUPA_2 = {
    "apikey": SUPABASE_KEY_2,
    "Authorization": f"Bearer {SUPABASE_KEY_2}",
}

# ==========================================
# FUNGSI HELPER
# ==========================================

def get_event_settings(slug: str):
    """Ambil Event ID, Filter Settings, dan Capture Settings dari Supabase 1"""
    rpc_url = f"{SUPABASE_URL_1}/rest/v1/rpc/get_event_by_slug"
    res_rpc = requests.post(rpc_url, headers=HEADERS_SUPA_1, json={"p_slug": slug})
    
    if res_rpc.status_code != 200 or not res_rpc.json():
        raise HTTPException(status_code=404, detail="Event slug tidak ditemukan.")
    
    event_data = res_rpc.json()[0]
    event_id = event_data['id']

    # Ambil Filter Settings
    filter_url = f"{SUPABASE_URL_1}/rest/v1/filter_settings?event_id=eq.{event_id}&select=enabled,prompt,model,resolution"
    res_filter = requests.get(filter_url, headers=HEADERS_SUPA_1)
    filter_settings = res_filter.json()[0] if res_filter.json() else {"enabled": False}

    # Ambil Capture Settings
    capture_url = f"{SUPABASE_URL_1}/rest/v1/capture_settings?event_id=eq.{event_id}&select=aspect_ratio"
    res_capture = requests.get(capture_url, headers=HEADERS_SUPA_1)
    capture_settings = res_capture.json()[0] if res_capture.json() else {"aspect_ratio": "1:1"}

    return {
        "event_id": event_id,
        "event_name": event_data.get('event_name', ''),
        "filter": filter_settings,
        "capture": capture_settings
    }

def apply_ai_filter(image_bytes: bytes, settings: dict):
    """Kirim gambar ke server AI jika Filter diaktifkan"""
    print("[INFO] Menerapkan Filter AI...")
    
    base64_img = base64.b64encode(image_bytes).decode('utf-8')
    data_uri = f"data:image/jpeg;base64,{base64_img}"
    
    prompt = settings['filter'].get('prompt', '').replace('\n', ' ')
    
    payload = {
        "image": data_uri,
        "prompt": prompt,
        "aspectRatio": settings['capture'].get('aspect_ratio', '1:1'),
        "eventId": settings['event_id'],
        "model": settings['filter'].get('model', ''),
        "resolution": settings['filter'].get('resolution', '')
    }

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "python-requests/2.31.0",
        "Accept": "*/*"
    }
    
    try:
        # Timeout ditingkatkan ke 60 detik jika tidak di Vercel Serverless
        res = requests.post(AI_SERVER_URL, json=payload, headers=headers, timeout=60)
        
        if res.status_code == 200 and len(res.content) > 0:
            print("[SUCCESS] Filter AI berhasil diterapkan oleh AI Server.")
            return res.content, True
        else:
            print(f"[ERROR] AI Server gagal dengan status {res.status_code}: {res.text[:100]}. Fallback ke gambar asli.")
            return image_bytes, False
            
    except requests.exceptions.Timeout:
        print("[WARNING] AI Server Timeout (>60s). Fallback ke gambar asli.")
        return image_bytes, False
    except Exception as e:
        print(f"[ERROR] Gagal memproses AI filter: {e}")
        return image_bytes, False

def upload_to_supabase_2(image_bytes: bytes):
    """Upload gambar ke Storage Supabase 2"""
    file_name = f"photo_{int(time.time())}_{uuid.uuid4().hex[:6]}.jpg"
    storage_url = f"{SUPABASE_URL_2}/storage/v1/object/{TARGET_BUCKET}/{file_name}"
    
    headers = HEADERS_SUPA_2.copy()
    headers["Content-Type"] = "image/jpeg"
    
    res = requests.post(storage_url, headers=headers, data=image_bytes)
    
    if res.status_code in [200, 201]:
        return file_name
    else:
        raise HTTPException(status_code=500, detail=f"Gagal upload ke storage: {res.text}")

def save_data_to_supabase_2(event_id: str, file_name: str, is_filtered: bool):
    """Simpan informasi/log ke Table Database Supabase 2"""
    table_url = f"{SUPABASE_URL_2}/rest/v1/{TARGET_TABLE}"
    
    headers = HEADERS_SUPA_2.copy()
    headers["Content-Type"] = "application/json"
    headers["Prefer"] = "return=representation"
    
    payload = {
        "event_id": event_id,
        "file_name": file_name,
        "is_ai_filtered": is_filtered,
        "uploaded_at": int(time.time())
    }
    
    res = requests.post(table_url, headers=headers, json=payload)
    if res.status_code not in [200, 201]:
        print(f"[WARNING] Gagal insert data ke tabel: {res.text}")

# ==========================================
# ENDPOINT UTAMA
# ==========================================

@app.post("/upload-image/{slug}")
async def process_camera_image(slug: str, image: UploadFile = File(...)):
    try:
        image_bytes = await image.read()
        print(f"[INFO] Menerima gambar untuk slug: {slug} (Size: {len(image_bytes)} bytes)")
        
        # 1. Ambil Pengaturan dari Supabase 1
        settings = get_event_settings(slug)
        print(f"[INFO] Event ID: {settings['event_id']}, Filter Enabled: {settings['filter'].get('enabled')}")
        
        is_filter_enabled = settings['filter'].get('enabled') is True
        is_filtered = False
        final_image = image_bytes
        
        # 2. Proses AI Filter HANYA JIKA Filter Diaktifkan (enabled == True)
        if is_filter_enabled:
            final_image, is_filtered = apply_ai_filter(image_bytes, settings)
        else:
            print("[INFO] AI Filter di-disable di Supabase. Menggunakan gambar asli.")
        
        # 3. Upload ke Supabase 2 Storage
        file_name = upload_to_supabase_2(final_image)
        print(f"[SUCCESS] Gambar terunggah: {file_name}")
        
        # 4. Simpan Log ke Tabel Supabase 2
        save_data_to_supabase_2(settings['event_id'], file_name, is_filtered)
        print(f"[SUCCESS] Log tersimpan dengan status is_ai_filtered = {is_filtered}")
        
        return JSONResponse(content={
            "status": "success", 
            "message": "Gambar berhasil diproses dan disimpan.",
            "file_name": file_name,
            "filter_enabled_in_db": is_filter_enabled,
            "is_filtered": is_filtered
        })

    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"error": e.detail})
    except Exception as e:
        print(f"[FATAL ERROR] {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})
