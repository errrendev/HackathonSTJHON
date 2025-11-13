import requests
import base64

# Read and encode the image
image_path = "./canvas_image_1740642767270.png"

with open(image_path, "rb") as image_file:
    base64_image = base64.b64encode(image_file.read()).decode('utf-8')

# Add the data URL prefix
base64_with_prefix = f"data:image/jpeg;base64,{base64_image}"

# Send request
response = requests.post(
    "http://localhost:8000/save-image",
    json={
        "image": base64_with_prefix,
        "prompt": "Describe this image in detail"
    }
)

print(response.json())