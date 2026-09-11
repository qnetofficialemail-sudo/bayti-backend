import os

BACKEND = r"C:\Users\Dell\Desktop\homemarketplace\backend"
studio_path = os.path.join(BACKEND, "routers", "studio.py")
content = open(studio_path, encoding="utf-8").read()

# Find the prompt suffix in the user_prompt and enhance it
old_suffix = '''Then write ONE detailed prompt starting with "A hyper-realistic professional fashion photograph of" that:
- States the exact color explicitly
- Describes all design details from the image
- Includes the model, background, shot style
- Ends with: "No text, no watermarks, no logos. AI-generated marketing visualization."'''

new_suffix = '''Then write ONE detailed prompt starting with "A hyper-realistic professional fashion photograph of" that:
- States the exact color explicitly (e.g. "deep crimson red", not just "red")
- Describes ALL visible design details from the image precisely
- Includes the model description, pose, background, lighting, shot style
- Specifies fabric feel: "soft fleece", "flowing chiffon", "structured cotton", etc.
- Mentions camera technical details at the end: "Shot on Sony A7R V, 85mm f/1.4 lens, shallow depth of field, tack sharp focus on clothing"
- Ends with: "Photorealistic, 8K resolution, professional fashion editorial. No text overlays, no watermarks, no extra logos beyond what is on the garment. AI-generated marketing visualization."

Important for maximum accuracy:
- If the garment has a graphic/print, describe it in exact detail so it is reproduced faithfully
- Specify the exact shade of every color (use paint/pantone-style names)
- Mention fabric weight if visible (heavyweight, lightweight, medium-weight)
- Include styling details: tucked/untucked, layered, accessories worn'''

if old_suffix in content:
    content = content.replace(old_suffix, new_suffix)
    open(studio_path, "w", encoding="utf-8").write(content)
    print("✅ Enhanced prompt quality instructions")
else:
    print("NOT FOUND — searching...")
    idx = content.find('Then write ONE detailed prompt')
    if idx >= 0:
        print(repr(content[idx:idx+200]))
