import cloudinary
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

def upload_application_doc(file_bytes: bytes, filename: str) -> str:
    """Upload seller application document to Cloudinary (public)."""
    import uuid
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "pdf"
    unique_id = str(uuid.uuid4())[:8]
    resource_type = "raw" if ext == "pdf" else "image"
    result = cloudinary.uploader.upload(
        file_bytes,
        folder="bayti/applications",
        public_id=f"doc_{unique_id}",
        overwrite=False,
        resource_type=resource_type,
    )
    return result["secure_url"]
