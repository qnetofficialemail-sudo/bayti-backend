import os

BACKEND = r'C:\Users\Dell\Desktop\homemarketplace\backend'
FRONTEND = r'C:\Users\Dell\Desktop\homemarketplace\frontend'

# 1. Patch sellers.py
sellers_path = os.path.join(BACKEND, 'routers', 'sellers.py')
sellers = open(sellers_path, encoding='utf-8').read()

old_endpoint = '@router.patch("/profile/edit")\nasync def edit_seller_profile(\n    shop_name: Optional[str] = None,'
new_endpoint = '@router.patch("/profile/edit")\nasync def edit_seller_profile(\n    shop_name: Optional[str] = Form(None),'

if 'sample_image_1: Optional[UploadFile]' not in sellers:
    # Add Form imports
    if 'Form' not in sellers:
        sellers = sellers.replace(
            'from fastapi import APIRouter, Depends, HTTPException',
            'from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile'
        )
    # Change params to Form()
    sellers = sellers.replace(
        'async def edit_seller_profile(\n    shop_name: Optional[str] = None,\n    description: Optional[str] = None,\n    area: Optional[str] = None,\n    city: Optional[str] = None,\n    whatsapp_number: Optional[str] = None,\n    instagram_handle: Optional[str] = None,\n    min_order_amount: Optional[float] = None,\n    db: Session = Depends(get_db),',
        'async def edit_seller_profile(\n    shop_name: Optional[str] = Form(None),\n    description: Optional[str] = Form(None),\n    area: Optional[str] = Form(None),\n    city: Optional[str] = Form(None),\n    whatsapp_number: Optional[str] = Form(None),\n    instagram_handle: Optional[str] = Form(None),\n    min_order_amount: Optional[float] = Form(None),\n    sample_image_1: Optional[UploadFile] = File(None),\n    sample_image_2: Optional[UploadFile] = File(None),\n    sample_image_3: Optional[UploadFile] = File(None),\n    db: Session = Depends(get_db),'
    )
    # Add image upload logic
    sellers = sellers.replace(
        '    if min_order_amount is not None: seller.min_order_amount = min_order_amount\n    db.commit()',
        '    if min_order_amount is not None: seller.min_order_amount = min_order_amount\n    from services.cloudinary_upload import upload_seller_logo\n    for i, img in enumerate([sample_image_1, sample_image_2, sample_image_3], 1):\n        if img and img.filename:\n            fb = await img.read()\n            url = upload_seller_logo(fb, img.filename)\n            setattr(seller, f"sample_image_{i}", url)\n    db.commit()'
    )
    open(sellers_path, 'w', encoding='utf-8').write(sellers)
    print("Done - sellers.py updated")
else:
    print("Skip - already updated")

# 2. Write EditShop.tsx
edit_path = os.path.join(FRONTEND, 'src', 'pages', 'EditShop.tsx')
content = open(edit_path, encoding='utf-8').read()

# Add image state after existing state declarations
old_state = '  const [form, setForm] = useState({ shop_name: "", description: "", area: "", city: "Dubai", whatsapp_number: "", instagram_handle: "", min_order_amount: "" });'
new_state = '  const [form, setForm] = useState({ shop_name: "", description: "", area: "", city: "Dubai", whatsapp_number: "", instagram_handle: "", min_order_amount: "" });\n  const [existingImages, setExistingImages] = useState<(string|null)[]>([null, null, null]);\n  const [newImages, setNewImages] = useState<(File|null)[]>([null, null, null]);\n  const [newPreviews, setNewPreviews] = useState<(string|null)[]>([null, null, null]);'

if 'existingImages' not in content:
    content = content.replace(old_state, new_state)

    # Load existing images from API
    old_load = '        setForm({'
    new_load = '        setExistingImages([myShop.sample_image_1 || null, myShop.sample_image_2 || null, myShop.sample_image_3 || null]);\n        setForm({'
    content = content.replace(old_load, new_load, 1)

    # Add handleImage helper before handleSubmit
    old_submit = '  const handleSubmit = async (e: React.FormEvent) => {'
    new_submit = '''  const handleNewImage = (i: number, file: File | null) => {
    const imgs = [...newImages]; const prevs = [...newPreviews];
    imgs[i] = file; prevs[i] = file ? URL.createObjectURL(file) : null;
    setNewImages(imgs); setNewPreviews(prevs);
  };

  const imgUrl = (img: string) => img.startsWith("http") ? img : `https://web-production-63685.up.railway.app${img}`;

  const handleSubmit = async (e: React.FormEvent) => {'''
    content = content.replace(old_submit, new_submit)

    # Change submit to use FormData
    old_api = '      await api.patch("/api/sellers/profile/edit", form);'
    new_api = '''      const data = new FormData();
      Object.entries(form).forEach(([k, v]) => { if (v !== "") data.append(k, v); });
      newImages.forEach((img, i) => { if (img) data.append(`sample_image_${i+1}`, img); });
      await api.patch("/api/sellers/profile/edit", data, { headers: { "Content-Type": "multipart/form-data" } });'''
    content = content.replace(old_api, new_api)

    # Add image upload UI before shop name field
    old_name_field = '        <div>\n          <label className="block text-sm font-medium text-gray-700 mb-1">{isArabic ? '
    new_img_ui = '''        {/* Shop images */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">{isArabic ? "\u0635\u0648\u0631 \u0627\u0644\u0645\u062a\u062c\u0631 (\u062d\u062a\u0649 3)" : "Shop Photos (up to 3)"}</label>
          <p className="text-xs text-gray-400 mb-3">{isArabic ? "\u062a\u0638\u0647\u0631 \u0641\u064a \u0635\u0641\u062d\u0629 \u0645\u062a\u062c\u0631\u0643 \u0644\u0644\u0639\u0645\u0644\u0627\u0621" : "Shown on your public shop page"}</p>
          <div className="grid grid-cols-3 gap-3">
            {[0,1,2].map(i => (
              <div key={i} className="space-y-1">
                <div className="aspect-square rounded-xl overflow-hidden border-2 border-dashed border-gray-200 flex items-center justify-center bg-gray-50">
                  {newPreviews[i]
                    ? <img src={newPreviews[i]!} alt="" className="w-full h-full object-cover" />
                    : existingImages[i]
                    ? <img src={imgUrl(existingImages[i]!)} alt="" className="w-full h-full object-cover" />
                    : <div className="text-center text-gray-300"><div className="text-3xl">\U0001f4f7</div><div className="text-xs mt-1">{i+1}</div></div>
                  }
                </div>
                <label className="block cursor-pointer">
                  <div className="text-center text-xs text-orange-500 hover:text-orange-600 py-1 border border-orange-200 rounded-lg hover:bg-orange-50 transition">
                    {isArabic ? "\u062a\u063a\u064a\u064a\u0631" : "Upload"}
                  </div>
                  <input type="file" accept="image/*" className="hidden" onChange={e => handleNewImage(i, e.target.files?.[0] || null)} />
                </label>
              </div>
            ))}
          </div>
        </div>

        <div>\n          <label className="block text-sm font-medium text-gray-700 mb-1">{isArabic ? '''

    if old_name_field in content:
        content = content.replace(old_name_field, new_img_ui, 1)
        print("Done - image UI added to EditShop")
    else:
        print("FAIL - name field not found in EditShop")
        idx = content.find('shop_name')
        print(repr(content[max(0,idx-50):idx+200]))

    open(edit_path, 'w', encoding='utf-8').write(content)
else:
    print("Skip - EditShop already updated")

print("All done")
