from py_vapid import Vapid
vapid = Vapid()
vapid.generate_keys()
print("VAPID_PRIVATE_KEY:", vapid.private_key.private_bytes(
    encoding=__import__("cryptography.hazmat.primitives.serialization", fromlist=["Encoding"]).Encoding.PEM,
    format=__import__("cryptography.hazmat.primitives.serialization", fromlist=["PrivateFormat"]).PrivateFormat.PKCS8,
    encryption_algorithm=__import__("cryptography.hazmat.primitives.serialization", fromlist=["NoEncryption"]).NoEncryption()
).decode())
print("VAPID_PUBLIC_KEY:", vapid.public_key.public_bytes(
    encoding=__import__("cryptography.hazmat.primitives.serialization", fromlist=["Encoding"]).Encoding.X962,
    format=__import__("cryptography.hazmat.primitives.serialization", fromlist=["PublicFormat"]).PublicFormat.UncompressedPoint
).hex())
