from py_vapid import Vapid
import base64, json

vapid = Vapid()
vapid.generate_keys()

# Get keys in base64url format (what browsers expect)
private_key = base64.urlsafe_b64encode(
    vapid.private_key.private_numbers().private_value.to_bytes(32, 'big')
).decode().rstrip('=')

public_key_bytes = vapid.public_key.public_bytes(
    encoding=__import__('cryptography.hazmat.primitives.serialization', fromlist=['Encoding']).Encoding.X962,
    format=__import__('cryptography.hazmat.primitives.serialization', fromlist=['PublicFormat']).PublicFormat.UncompressedPoint
)
public_key = base64.urlsafe_b64encode(public_key_bytes).decode().rstrip('=')

print(f"VAPID_PRIVATE_KEY={private_key}")
print(f"VAPID_PUBLIC_KEY={public_key}")

# Save to file for easy copy
with open('vapid_keys.txt', 'w') as f:
    f.write(f"VAPID_PRIVATE_KEY={private_key}\n")
    f.write(f"VAPID_PUBLIC_KEY={public_key}\n")
print("\nSaved to vapid_keys.txt")
