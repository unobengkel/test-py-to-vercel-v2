import requests

# Masukkan slug: kamera-disposable
url = "https://test-py-to-vercel-v2.vercel.app/upload-image/kamera-disposable"
image_path = "test_photo.jpg"

with open(image_path, "rb") as img_file:
    files = {"image": ("test_photo.jpg", img_file, "image/jpeg")}
    
    print("Mengirim gambar ke Vercel...")
    response = requests.post(url, files=files)
    
    print("Status Code:", response.status_code)
    if response.status_code == 200:
        print("Response JSON:", response.json())
    else:
        print("Error Response Text:", response.text)
