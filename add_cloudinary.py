import os

BACKEND = r'C:\Users\Dell\Desktop\homemarketplace\backend'

# ── 1. Add cloudinary to requirements.txt ──
req_path = os.path.join(BACKEND, 'requirements.txt')
content = open(req_path, encoding='utf-8').read()
if 'cloudinary' not in content:
    content += '\ncloudinary==1.36.0\n'
    open(req_path, 'w', encoding='utf-8').write(content)
    print("✅ 1. cloudinary added to requirements.txt")
else:
    print("✅ 1. cloudinary already in requirements.txt")

# ── 2. Create services/cloudinary_upload.py ──
cloudinary_service = '''import cloudinary
import cloudinary.uploader
import os

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME", "widblmd7"),
    api_key=os.getenv("CLOUDINARY_API_KEY", "696692571769376"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET", "jYl_Z74q6YTI5RPs_wiWQ5p4n74"),
    secure=True
)

def upload_product_image(file_bytes: bytes, filename: str) -> str:
    """Upload image to Cloudinary and return the secure URL."""
    result = cloudinary.uploader.upload(
        file_bytes,
        folder="bayti/products",
        public_id=filename.rsplit(".", 1)[0],
        overwrite=True,
        resource_type="image",
        transformation=[
            {"width": 800, "height": 800, "crop": "fill", "gravity": "auto"},
            {"quality": "auto", "fetch_format": "auto"}
        ]
    )
    return result["secure_url"]

def upload_seller_logo(file_bytes: bytes, filename: str) -> str:
    """Upload seller logo to Cloudinary."""
    result = cloudinary.uploader.upload(
        file_bytes,
        folder="bayti/logos",
        public_id=filename.rsplit(".", 1)[0],
        overwrite=True,
        resource_type="image",
        transformation=[
            {"width": 400, "height": 400, "crop": "fill", "gravity": "auto"},
            {"quality": "auto", "fetch_format": "auto"}
        ]
    )
    return result["secure_url"]
'''

svc_path = os.path.join(BACKEND, 'services', 'cloudinary_upload.py')
open(svc_path, 'w', encoding='utf-8').write(cloudinary_service)
print("✅ 2. services/cloudinary_upload.py created")

# ── 3. Update routers/products.py to use Cloudinary ──
products_path = os.path.join(BACKEND, 'routers', 'products.py')
content = open(products_path, encoding='utf-8').read()

# Replace local file imports/handling with Cloudinary
old1 = '''from services.translation import translate_product_to_arabic
import shutil, os, uuid

router = APIRouter(prefix="/api/products", tags=["products"])

UPLOAD_DIR = "uploads/products"
os.makedirs(UPLOAD_DIR, exist_ok=True)'''

new1 = '''from services.translation import translate_product_to_arabic
from services.cloudinary_upload import upload_product_image
import uuid

router = APIRouter(prefix="/api/products", tags=["products"])'''

content = content.replace(old1, new1)

# Replace local file save in create_product
old2 = '''    image_url = None
    if image:
        ext = image.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as f:
            shutil.copyfileobj(image.file, f)
        image_url = f"/uploads/products/{filename}"'''

new2 = '''    image_url = None
    if image:
        ext = image.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{ext}"
        file_bytes = await image.read()
        image_url = upload_product_image(file_bytes, filename)'''

content = content.replace(old2, new2)

# Replace local file save in update_product
old3 = '''    if image:
        ext = image.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as f:
            shutil.copyfileobj(image.file, f)
        product.image_url = f"/uploads/products/{filename}"'''

new3 = '''    if image:
        ext = image.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{ext}"
        file_bytes = await image.read()
        product.image_url = upload_product_image(file_bytes, filename)'''

content = content.replace(old3, new3)

# Make create_product and update_product async
content = content.replace('def create_product(', 'async def create_product(')
content = content.replace('def update_product(', 'async def update_product(')

open(products_path, 'w', encoding='utf-8').write(content)
print("✅ 3. routers/products.py updated to use Cloudinary")

# ── 4. Update frontend: fix image URLs (Cloudinary returns full URL, not relative path) ──
print("\n✅ All backend changes done!")
print("⚠️  Frontend: image_url will now be a full Cloudinary URL, not a relative path.")
print("   Need to update Home.tsx and ProductDetail.tsx to not prepend Railway URL.")
