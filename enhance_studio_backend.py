import os

BACKEND = r"C:\Users\Dell\Desktop\homemarketplace\backend"
studio_path = os.path.join(BACKEND, "routers", "studio.py")
content = open(studio_path, encoding="utf-8").read()

# Add new form parameters
old_params = '''    output_format: str = Form("product_square"),
    image: UploadFile = File(...),'''

new_params = '''    output_format: str = Form("product_square"),
    model_size:    str = Form("regular"),
    lighting:      str = Form("soft_natural"),
    season:        str = Form("none"),
    pose:          str = Form("standing_neutral"),
    extra_notes:   str = Form(""),
    image: UploadFile = File(...),'''

if old_params in content:
    content = content.replace(old_params, new_params)
    print("✅ Added new form params")
else:
    print("PARAMS NOT FOUND")

# Update user_prompt to include new options
old_prompt_build = '''    model_desc   = MODEL_LABELS.get(model_style, MODEL_LABELS["female_gulf_modern"])
    bg_desc      = BG_LABELS.get(background, BG_LABELS["white_studio"])
    framing_desc = FRAMING_LABELS.get(framing, FRAMING_LABELS["full_body"])
    format_desc  = FORMAT_LABELS.get(output_format, FORMAT_LABELS["product_square"])'''

new_prompt_build = '''    model_desc   = MODEL_LABELS.get(model_style, MODEL_LABELS["female_gulf_modern"])
    bg_desc      = BG_LABELS.get(background, BG_LABELS["white_studio"])
    framing_desc = FRAMING_LABELS.get(framing, FRAMING_LABELS["full_body"])
    format_desc  = FORMAT_LABELS.get(output_format, FORMAT_LABELS["product_square"])

    size_map = {"slim": "slim build", "regular": "regular/average build", "curvy": "curvy/full-figured build"}
    light_map = {"soft_natural": "soft natural daylight", "golden_hour": "warm golden hour sunset light", "studio_bright": "bright clean studio lighting", "moody_dark": "moody dramatic low-key lighting"}
    pose_map = {"standing_neutral": "standing in a natural neutral pose", "walking": "walking dynamically toward the camera", "sitting_elegant": "sitting elegantly", "looking_side": "looking slightly to the side in a candid pose"}
    season_map = {"none": "", "summer": "summer vibes, bright and airy", "winter": "winter cozy atmosphere", "ramadan": "Ramadan elegant festive mood, subtle lantern or crescent elements in background", "eid": "Eid celebration joyful elegant mood"}

    size_desc    = size_map.get(model_size, "regular/average build")
    light_desc   = light_map.get(lighting, "soft natural daylight")
    pose_desc    = pose_map.get(pose, "standing in a natural neutral pose")
    season_desc  = season_map.get(season, "")
    extra_desc   = extra_notes.strip() if extra_notes else ""'''

if old_prompt_build in content:
    content = content.replace(old_prompt_build, new_prompt_build)
    print("✅ Added new option mappings")
else:
    print("PROMPT BUILD NOT FOUND")

# Update user_prompt to use new fields
old_user_prompt = '''The generated image should show:
- Model: {model_desc}
- Background: {bg_desc}  
- Shot: {framing_desc}, {format_desc}
- Style: professional commercial fashion photography, editorial quality'''

new_user_prompt = '''The generated image should show:
- Model: {model_desc}, {size_desc}
- Pose: {pose_desc}
- Background: {bg_desc}
- Lighting: {light_desc}
- Shot: {framing_desc}, {format_desc}
- Style: professional commercial fashion photography, editorial quality{season_clause}{extra_clause}'''.replace(
    '{season_clause}', '''
- Season/Mood: {season_desc}''' if True else ''
).replace(
    '{extra_clause}', '''
- Special notes: {extra_desc}''' if True else ''
)

# simpler approach
old_user_prompt2 = '''The generated image should show:
- Model: {model_desc}
- Background: {bg_desc}  
- Shot: {framing_desc}, {format_desc}
- Style: professional commercial fashion photography, editorial quality'''

new_user_prompt2 = '''The generated image should show:
- Model: {model_desc}, {size_desc}
- Pose: {pose_desc}
- Background: {bg_desc}
- Lighting: {light_desc}
- Shot: {framing_desc}, {format_desc}
- Season/Mood: {season_desc if season_desc else "timeless, no specific season"}
- Style: professional commercial fashion photography, editorial quality
- Special requests: {extra_desc if extra_desc else "none"}'''

if old_user_prompt2 in content:
    content = content.replace(old_user_prompt2, new_user_prompt2)
    print("✅ Updated user prompt with new fields")
else:
    print("USER PROMPT NOT FOUND — trying direct replacement")
    idx = content.find("The generated image should show:")
    if idx >= 0:
        end = content.find("Extract from the image:", idx)
        old_block = content[idx:end]
        new_block = """The generated image should show:
- Model: {model_desc}, {size_desc}
- Pose: {pose_desc}
- Background: {bg_desc}
- Lighting: {light_desc}
- Shot: {framing_desc}, {format_desc}
- Season/Mood: {season_desc if season_desc else "timeless, no specific season"}
- Style: professional commercial fashion photography, editorial quality
- Special requests: {extra_desc if extra_desc else "none"}

"""
        content = content[:idx] + new_block + content[end:]
        print("✅ Updated user prompt (direct)")

open(studio_path, "w", encoding="utf-8").write(content)
print("\nDone!")
