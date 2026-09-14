path = "models/user.py"
with open(path, "rb") as f:
    c = f.read().decode("utf-8")
has_crlf = "\r\n" in c
c = c.replace("\r\n", "\n")
n = 0

old = '    description = Column(Text, nullable=True)\n    area = Column(String, nullable=False)'
new = '    description = Column(Text, nullable=True)\n    description_ar = Column(Text, nullable=True)\n    area = Column(String, nullable=False)'

if old in c: c=c.replace(old,new); n+=1; print("OK description_ar in SellerProfile model")
else: print("MISS")

if has_crlf:
    c = c.replace("\n", "\r\n")
with open(path, "wb") as f:
    f.write(c.encode("utf-8"))
print(f"Done {n}/1 models/user.py")
