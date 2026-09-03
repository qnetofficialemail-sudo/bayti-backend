import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
from_number = os.getenv("TWILIO_WHATSAPP_FROM", "+14155238886")

def send_whatsapp(to_phone: str, message: str) -> bool:
    """Send a WhatsApp message via Twilio sandbox."""
    try:
        if not account_sid or not auth_token:
            print("Twilio credentials not configured")
            return False
        client = Client(account_sid, auth_token)
        msg = client.messages.create(
            from_=f"whatsapp:{from_number}",
            to=f"whatsapp:{to_phone}",
            body=message
        )
        print(f"WhatsApp sent: {msg.sid}")
        return True
    except Exception as e:
        print(f"WhatsApp error: {e}")
        return False

def notify_seller_new_order(seller_phone: str, seller_name: str, buyer_name: str,
                             items: list, total: float, area: str, notes: str = None):
    """Notify seller when a new order arrives."""
    items_text = ", ".join([f"{item['quantity']}x {item['name']}" for item in items])
    message = (
        f"🛍️ New order on HomeMarket UAE!\n\n"
        f"Hello {seller_name},\n"
        f"📦 Order from: {buyer_name}\n"
        f"🍽️ Items: {items_text}\n"
        f"📍 Delivery to: {area}\n"
        f"💰 Total: AED {total:.2f}\n"
    )
    if notes:
        message += f"📝 Note: {notes}\n"
    message += "\nLog in to HomeMarket UAE to confirm this order."
    return send_whatsapp(seller_phone, message)

def notify_buyer_order_confirmed(buyer_phone: str, buyer_name: str,
                                  shop_name: str, prep_time: int = 60):
    """Notify buyer when seller confirms their order."""
    message = (
        f"✅ Your order is confirmed!\n\n"
        f"Hi {buyer_name},\n"
        f"🏠 {shop_name} has confirmed your order.\n"
        f"⏱️ Estimated prep time: {prep_time} minutes\n\n"
        f"We\'ll notify you when it\'s ready for delivery."
    )
    return send_whatsapp(buyer_phone, message)

def notify_buyer_order_ready(buyer_phone: str, buyer_name: str, shop_name: str):
    """Notify buyer when order is out for delivery."""
    message = (
        f"🚴 Your order is on the way!\n\n"
        f"Hi {buyer_name},\n"
        f"Your order from {shop_name} is out for delivery.\n"
        f"Please be available to receive it. 🏠"
    )
    return send_whatsapp(buyer_phone, message)
