path = "routers/sellers.py"
with open(path, "rb") as f:
    c = f.read().decode("utf-8")
has_crlf = "\r\n" in c
c = c.replace("\r\n", "\n")
n = 0

# 1. Add description_ar and logo to edit endpoint signature
old1 = '''    shop_name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    area: Optional[str] = Form(None),'''
new1 = '''    shop_name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    description_ar: Optional[str] = Form(None),
    area: Optional[str] = Form(None),'''

if old1 in c: c=c.replace(old1,new1); n+=1; print("OK edit signature description_ar")
else: print("MISS edit signature description_ar")

old2 = '''    sample_image_1: Optional[UploadFile] = File(None),
    sample_image_2: Optional[UploadFile] = File(None),
    sample_image_3: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_seller)
):
    seller = db.query(SellerProfile).filter(SellerProfile.user_id == current_user.id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller profile not found")
    if shop_name is not None: seller.shop_name = shop_name
    if description is not None: seller.description = description'''
new2 = '''    logo: Optional[UploadFile] = File(None),
    sample_image_1: Optional[UploadFile] = File(None),
    sample_image_2: Optional[UploadFile] = File(None),
    sample_image_3: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_seller)
):
    seller = db.query(SellerProfile).filter(SellerProfile.user_id == current_user.id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller profile not found")
    if shop_name is not None: seller.shop_name = shop_name
    if description is not None:
        seller.description = description
        # Auto-translate description to Arabic if not provided
        if not description_ar:
            try:
                import os, requests as _req
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if api_key:
                    resp = _req.post(
                        "https://api.anthropic.com/v1/messages",
                        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                        json={"model": "claude-haiku-4-5-20251001", "max_tokens": 300,
                              "messages": [{"role": "user", "content": f"Translate this UAE shop description to Arabic. Return ONLY the translation:\n\n{description}"}]},
                        timeout=15,
                    )
                    seller.description_ar = resp.json().get("content", [{}])[0].get("text", "").strip()
            except: pass
    if description_ar is not None: seller.description_ar = description_ar'''

if old2 in c: c=c.replace(old2,new2); n+=1; print("OK edit body with logo and auto-translate")
else: print("MISS edit body")

# 2. Add logo upload after sample images
old3 = '''    from services.cloudinary_upload import upload_seller_logo as _usl
    for i, img in enumerate([sample_image_1, sample_image_2, sample_image_3], 1):
        if img and img.filename:
            fb = await img.read()
            url = _usl(fb, img.filename)
            setattr(seller, f"sample_image_{i}", url)'''
new3 = '''    from services.cloudinary_upload import upload_seller_logo as _usl
    if logo and logo.filename:
        fb = await logo.read()
        seller.logo_url = _usl(fb, logo.filename)
    for i, img in enumerate([sample_image_1, sample_image_2, sample_image_3], 1):
        if img and img.filename:
            fb = await img.read()
            url = _usl(fb, img.filename)
            setattr(seller, f"sample_image_{i}", url)'''

if old3 in c: c=c.replace(old3,new3); n+=1; print("OK logo upload")
else: print("MISS logo upload")

# 3. Add description_ar to public endpoint
old4 = '''        "description": seller.description,
        "area": seller.area,'''
new4 = '''        "description": seller.description,
        "description_ar": getattr(seller, "description_ar", None),
        "area": seller.area,'''

if old4 in c: c=c.replace(old4,new4); n+=1; print("OK public endpoint description_ar")
else: print("MISS public endpoint description_ar")

if has_crlf:
    c = c.replace("\n", "\r\n")
with open(path, "wb") as f:
    f.write(c.encode("utf-8"))
print(f"\nDone {n}/4 sellers.py")
