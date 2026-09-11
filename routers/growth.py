from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, func
from core.database import get_db, Base
from core.auth import get_current_user
from datetime import datetime
import anthropic, os, json

router = APIRouter(prefix="/api/growth", tags=["growth"])

# ── Model ────────────────────────────────────────────────────────────
class OutreachAccount(Base):
    __tablename__ = "outreach_accounts"
    id           = Column(Integer, primary_key=True)
    username     = Column(String, unique=True, nullable=False)
    display_name = Column(String, default="")
    category     = Column(String, default="")
    emirate      = Column(String, default="")
    product_note = Column(String, default="")
    followers    = Column(String, default="")
    status       = Column(String, default="new")
    # new | contacted | replied | interested | confirmed | not_interested
    notes        = Column(Text, default="")
    last_message = Column(Text, default="")
    contacted_at = Column(DateTime, nullable=True)
    replied_at   = Column(DateTime, nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    follow_up_due= Column(DateTime, nullable=True)
    created_at   = Column(DateTime, default=datetime.utcnow)

class OutreachMessage(Base):
    __tablename__ = "outreach_messages"
    id         = Column(Integer, primary_key=True)
    account_id = Column(Integer, nullable=False)
    message    = Column(Text, nullable=False)
    msg_type   = Column(String, default="first")  # first | followup1 | followup2 | objection
    created_at = Column(DateTime, default=datetime.utcnow)

# ── Startup migration ─────────────────────────────────────────────────
def migrate_growth_tables(engine):
    Base.metadata.create_all(bind=engine)

# ── Seed initial accounts ─────────────────────────────────────────────
INITIAL_ACCOUNTS = [
    {"username": "byher.bougie",      "display_name": "Bougie by Her",      "category": "شموع وهدايا",       "emirate": "دبي",     "product_note": "شموع يدوية مستدامة قابلة لإعادة التعبئة"},
    {"username": "shopcuratehome",    "display_name": "Curate Home",        "category": "ديكور وهدايا وحرف", "emirate": "دبي",     "product_note": "منتجات منزلية وهدايا مصنوعة يدوياً"},
    {"username": "ae.plantstudio",    "display_name": "Plant Studio AE",    "category": "نباتات وديكور",     "emirate": "دبي",     "product_note": "نباتات وأحواض وإكسسوارات ديكور"},
    {"username": "3us.of.all",        "display_name": "3 of Us",            "category": "حلويات وكيك",       "emirate": "أبوظبي",  "product_note": "كيك وحلويات للمناسبات"},
    {"username": "kitchen_homebakery","display_name": "Home Kitchen Bakery","category": "أغذية ومخبوزات",    "emirate": "غير محدد","product_note": "أطباق منزلية وحلويات مع توصيل"},
    {"username": "me.plantstudio",    "display_name": "Me Plant Shop",      "category": "نباتات",            "emirate": "دبي",     "product_note": "نباتات وأحواض مع توصيل داخل الإمارات"},
    {"username": "crazyart___",       "display_name": "Crazy Art",          "category": "حرف وهدايا",        "emirate": "الإمارات","product_note": "منتجات مخصصة وتوصيل في الإمارات"},
    {"username": "allthatdori",       "display_name": "All That Dori",      "category": "مجوهرات يدوية",     "emirate": "دبي",     "product_note": "مجوهرات مصنوعة يدوياً بمنتجات مميزة"},
    {"username": "bilarabi",          "display_name": "Bil Arabi",          "category": "مجوهرات عربية",     "emirate": "دبي",     "product_note": "قطع مخصصة تحمل رسائل عربية"},
    {"username": "imaarathelabel",    "display_name": "Imaarat The Label",  "category": "عبايات",            "emirate": "دبي",     "product_note": "عبايات مصممة ومصنوعة في الإمارات"},
    {"username": "abayas.arva",       "display_name": "Arva Abayas",        "category": "عبايات وأزياء",     "emirate": "دبي",     "product_note": "عبايات فاخرة مع شحن"},
    {"username": "skinstoryme",       "display_name": "Skin Store Me",      "category": "تجميل وعناية",      "emirate": "دبي",     "product_note": "منتجات تجميل نباتية"},
    {"username": "thehomeae",         "display_name": "The Home AE",        "category": "أثاث وديكور",       "emirate": "دبي",     "product_note": "أثاث وديكور منزلي فاخر"},
    {"username": "byher.bougie",      "display_name": "Bougie by Her",      "category": "شموع وهدايا",       "emirate": "دبي",     "product_note": "شموع يدوية مستدامة"},
    {"username": "fixdessertchocolatier","display_name":"Fix Dessert",      "category": "شوكوالتة وحلويات",  "emirate": "دبي",     "product_note": "شوكوالتة وحلويات فاخرة"},
    {"username": "mirzamchocolate",   "display_name": "Mirzam Chocolate",   "category": "شوكوالتة وهدايا",   "emirate": "دبي",     "product_note": "شوكوالتة محلية صناعية"},
    {"username": "camelsoapfactory",  "display_name": "Camel Soap Factory", "category": "عناية وهدايا",      "emirate": "دبي",     "product_note": "صابون وعناية من حليب الإبل"},
    {"username": "bouguessa",         "display_name": "Bouguessa",          "category": "أزياء نسائية",      "emirate": "دبي",     "product_note": "أزياء مقرها دبي"},
    {"username": "scentlibraryofficial","display_name":"Scent Library",     "category": "عطور وهدايا",       "emirate": "دبي",     "product_note": "دار عطور إماراتية"},
    {"username": "dxb_roasterscoffee","display_name": "DXB Roasters",      "category": "قهوة مختصة",        "emirate": "دبي",     "product_note": "قهوة مختصة تأسست في دبي"},
]

# ── CRUD endpoints ────────────────────────────────────────────────────

@router.get("/accounts")
def get_accounts(status: str = None, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    q = db.query(OutreachAccount)
    if status:
        q = q.filter(OutreachAccount.status == status)
    return q.order_by(OutreachAccount.created_at.desc()).all()

@router.post("/accounts")
def add_account(data: dict, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    acc = OutreachAccount(**{k: v for k, v in data.items() if k in OutreachAccount.__table__.columns.keys()})
    db.add(acc)
    db.commit()
    db.refresh(acc)
    return acc

@router.patch("/accounts/{account_id}")
def update_account(account_id: int, data: dict, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    acc = db.query(OutreachAccount).filter(OutreachAccount.id == account_id).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Not found")
    for k, v in data.items():
        if hasattr(acc, k):
            setattr(acc, k, v)
    # Auto-set timestamps
    if data.get("status") == "contacted" and not acc.contacted_at:
        acc.contacted_at = datetime.utcnow()
    if data.get("status") == "replied" and not acc.replied_at:
        acc.replied_at = datetime.utcnow()
    if data.get("status") == "confirmed" and not acc.confirmed_at:
        acc.confirmed_at = datetime.utcnow()
    db.commit()
    db.refresh(acc)
    return acc

@router.delete("/accounts/{account_id}")
def delete_account(account_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    acc = db.query(OutreachAccount).filter(OutreachAccount.id == account_id).first()
    if acc:
        db.delete(acc)
        db.commit()
    return {"ok": True}

@router.get("/stats")
def get_stats(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    total    = db.query(OutreachAccount).count()
    statuses = db.query(OutreachAccount.status, func.count()).group_by(OutreachAccount.status).all()
    status_map = {s: c for s, c in statuses}
    # Follow-ups due today
    from datetime import date
    today = datetime.utcnow().date()
    due_today = db.query(OutreachAccount).filter(
        OutreachAccount.status.in_(["contacted"]),
        func.date(OutreachAccount.contacted_at) <= str(today)
    ).count()
    return {
        "total": total,
        "new": status_map.get("new", 0),
        "contacted": status_map.get("contacted", 0),
        "replied": status_map.get("replied", 0),
        "interested": status_map.get("interested", 0),
        "confirmed": status_map.get("confirmed", 0),
        "not_interested": status_map.get("not_interested", 0),
        "due_today": due_today,
        "goal": 20,
        "progress_pct": round((status_map.get("confirmed", 0) / 20) * 100),
    }

@router.post("/generate-message")
def generate_message(data: dict, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="AI not configured")
    username     = data.get("username", "")
    display_name = data.get("display_name", "")
    category     = data.get("category", "")
    product_note = data.get("product_note", "")
    msg_type     = data.get("msg_type", "first")  # first | followup1 | followup2 | objection
    objection    = data.get("objection", "")
    tone         = data.get("tone", "formal")  # formal | warm

    type_instructions = {
        "first":     "رسالة تواصل أولى — أذكر منتجاً محدداً، اعرض فرصة الانضمام المبكر كأحد أول 10 بائعين، واذكر استوديو بيتي كهدية مجانية. اطلب فقط الإذن بإرسال التفاصيل.",
        "followup1": "متابعة أولى بعد 3-4 أيام — لطيفة ومختصرة، لا ضغط، ذكّر بالرسالة السابقة وأكد أنه لا يوجد أي التزام.",
        "followup2": "متابعة أخيرة وأخيرة — محترمة جداً، أخبرهم أنها آخر رسالة، اترك باباً مفتوحاً للمستقبل.",
        "objection": f"رد على اعتراض: '{objection}' — إجابة صادقة وواضحة بدون وعود مضاعفة.",
    }

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=600,
        system="""أنت مسؤول التواصل في فريق بيتي — منصة إماراتية لدعم المنتجات والمشاريع المحلية.
اكتب بالعربية الفصحى الخفيفة. الأسلوب: دافئ، احترافي، إنساني.
لا تبالغ في المديح. لا تعد بمبيعات مضمونة. الجمل قصيرة ومباشرة.
بيتي مميزات: ذكاء اصطناعي يكتب وصف المنتج، استوديو ذكي يولّد صور تسويقية مجاناً، مستشار تسعير، وصول لجمهور الإمارات، مجاني في المرحلة التجريبية.
رابط التسجيل: bayti-frontend-three.vercel.app/sell""",
        messages=[{"role": "user", "content": f"""اكتب رسالة إنستقرام للحساب @{username} ({display_name}).
المجال: {category}
ملاحظة عن المنتج: {product_note}
نوع الرسالة: {type_instructions.get(msg_type, type_instructions["first"])}
اكتب الرسالة فقط بدون أي مقدمة أو شرح."""}]
    )
    message = response.content[0].text.strip()
    # Save to DB
    acc = db.query(OutreachAccount).filter(OutreachAccount.username == username).first()
    if acc:
        msg_obj = OutreachMessage(account_id=acc.id, message=message, msg_type=msg_type)
        db.add(msg_obj)
        acc.last_message = message
        db.commit()
    return {"message": message}

@router.post("/daily-brief")
def get_daily_brief(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    stats = get_stats(db=db, current_user=current_user)
    # Accounts needing follow-up
    due = db.query(OutreachAccount).filter(OutreachAccount.status == "contacted").limit(3).all()
    due_names = [f"@{a.username}" for a in due]
    # Best performing category
    confirmed = db.query(OutreachAccount).filter(OutreachAccount.status.in_(["confirmed","interested"])).all()
    cat_counts = {}
    for a in confirmed:
        cat_counts[a.category] = cat_counts.get(a.category, 0) + 1
    best_cat = max(cat_counts, key=cat_counts.get) if cat_counts else "لم تُحدد بعد"

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400,
        messages=[{"role": "user", "content": f"""أنت مدير النمو في بيتي. اكتب ملخصاً يومياً ذكياً بالعربية الفصحى (5-7 جمل قصيرة) يتضمن:
١. توصية واحدة واضحة بناءً على هذه البيانات
٢. فئة تستحق الاستهداف اليوم مع سبب

البيانات:
- إجمالي الحسابات: {stats["total"]}
- تواصلنا معهم: {stats["contacted"]}
- ردوا: {stats["replied"]}  
- مهتمون: {stats["interested"]}
- مؤكدون: {stats["confirmed"]} من أصل 20
- ينتظرون متابعة: {due_names}
- أفضل فئة تجاوباً: {best_cat}

اكتب التوصية مباشرة بدون عناوين."""}]
    )
    return {
        "brief": response.content[0].text.strip(),
        "stats": stats,
        "due_followups": due_names,
        "best_category": best_cat,
    }

@router.post("/seed-accounts")
def seed_accounts(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    added = 0
    for acc_data in INITIAL_ACCOUNTS:
        exists = db.query(OutreachAccount).filter(OutreachAccount.username == acc_data["username"]).first()
        if not exists:
            db.add(OutreachAccount(**acc_data))
            added += 1
    db.commit()
    return {"added": added, "message": f"تم إضافة {added} حساب"}

@router.get("/objections")
def get_objections(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return [
        {"q": "ما الرسوم أو العمولة؟",
         "a": "نحن في مرحلة الاستكشاف حالياً، والانضمام المبكر مجاني تماماً. هدفنا بناء التجربة معكم وتحديد الرسوم العادلة لاحقاً."},
        {"q": "أبيع جيداً عبر إنستقرام، لماذا أحتاجكم؟",
         "a": "بيتي ليست بديلاً لإنستقرام، بل قناة اكتشاف إضافية تضع منتجاتكم أمام جمهور يبحث خصيصاً عن المحلي."},
        {"q": "ليس لدي وقت لإدارة منصة أخرى.",
         "a": "صممنا عملية الانضمام لتكون بسيطة جداً. نحن نتولى الجزء التقني، وكل ما تحتاجونه هو الموافقة على عرض منتجاتكم."},
        {"q": "هل تضمنون لي المبيعات؟",
         "a": "لا نعد بمبيعات مضمونة، لكننا نوفر قناة اكتشاف وظهوراً احترافياً أمام جمهور مناسب."},
        {"q": "هل المنصة جاهزة؟",
         "a": "نحن نبني النسخة الأولى مع مجموعة محدودة من البائعين، ولهذا نبحث عن شركاء يشاركوننا الملاحظات قبل التوسع."},
        {"q": "هل أحتاج إلى تغيير طريقة عملي؟",
         "a": "لا. نبدأ بمعلومات المنتجات والصور والبيانات الأساسية، ونحاول جعل المشاركة بأقل جهد ممكن."},
        {"q": "لست مهتمة الآن.",
         "a": "نحترم ذلك تماماً. يسعدنا التواصل معكم مستقبلاً عندما يكون الوقت مناسباً."},
    ]
