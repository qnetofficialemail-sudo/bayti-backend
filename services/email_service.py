import os
import requests

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
FROM_EMAIL = "noreply@bayti.ink"
FROM_NAME = "Bayti بيتي"

def send_email(to: str, subject: str, html: str) -> bool:
    """Send email via Resend API."""
    if not RESEND_API_KEY:
        print("RESEND_API_KEY not set - skipping email")
        return False
    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": f"{FROM_NAME} <{FROM_EMAIL}>",
                "to": [to],
                "subject": subject,
                "html": html,
            },
            timeout=10,
        )
        if response.status_code == 200:
            print(f"Email sent to {to}")
            return True
        else:
            print(f"Email failed: {response.status_code} {response.text}")
            return False
    except Exception as e:
        print(f"Email error: {e}")
        return False


def send_application_received(to: str, name: str) -> bool:
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
      <div style="background: #FF5A1F; padding: 24px; border-radius: 12px 12px 0 0; text-align: center;">
        <h1 style="color: white; margin: 0; font-size: 28px;">🏠 Bayti بيتي</h1>
      </div>
      <div style="background: #fff7ed; padding: 32px; border-radius: 0 0 12px 12px; border: 1px solid #fed7aa;">
        <h2 style="color: #1f2937;">Application Received! 🎉</h2>
        <p style="color: #4b5563;">Hi {name},</p>
        <p style="color: #4b5563;">Thank you for applying to sell on Bayti! We have received your application and our team will review it shortly.</p>
        <p style="color: #4b5563;">We will get back to you within 2-3 business days with our decision.</p>
        <hr style="border: none; border-top: 1px solid #fed7aa; margin: 24px 0;">
        <p style="color: #9ca3af; font-size: 14px;">Bayti — UAE's Local Products Marketplace</p>
        <p style="color: #9ca3af; font-size: 12px;" dir="rtl">بيتي — سوق المنتجات المحلية في الإمارات</p>
      </div>
    </div>
    """
    return send_email(to, "Application Received - Bayti بيتي", html)


def send_application_approved(to: str, name: str, registration_link: str) -> bool:
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
      <div style="background: #FF5A1F; padding: 24px; border-radius: 12px 12px 0 0; text-align: center;">
        <h1 style="color: white; margin: 0; font-size: 28px;">🏠 Bayti بيتي</h1>
      </div>
      <div style="background: #fff7ed; padding: 32px; border-radius: 0 0 12px 12px; border: 1px solid #fed7aa;">
        <h2 style="color: #1f2937;">Congratulations! Your Application is Approved ✅</h2>
        <p style="color: #4b5563;">Hi {name},</p>
        <p style="color: #4b5563;">Great news! Your application to sell on Bayti has been approved. Click the button below to complete your registration and set up your shop.</p>
        <div style="text-align: center; margin: 32px 0;">
          <a href="{registration_link}" style="background: #FF5A1F; color: white; padding: 14px 32px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 16px;">
            Complete Registration →
          </a>
        </div>
        <p style="color: #6b7280; font-size: 14px;">Or copy this link: <a href="{registration_link}" style="color: #FF5A1F;">{registration_link}</a></p>
        <p style="color: #ef4444; font-size: 13px;">⚠️ This link is unique to you. Do not share it with others.</p>
        <hr style="border: none; border-top: 1px solid #fed7aa; margin: 24px 0;">
        <p style="color: #9ca3af; font-size: 14px;">Bayti — UAE's Local Products Marketplace</p>
      </div>
    </div>
    """
    return send_email(to, "Your Bayti Application is Approved! 🎉", html)


def send_application_rejected(to: str, name: str) -> bool:
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
      <div style="background: #FF5A1F; padding: 24px; border-radius: 12px 12px 0 0; text-align: center;">
        <h1 style="color: white; margin: 0; font-size: 28px;">🏠 Bayti بيتي</h1>
      </div>
      <div style="background: #fff7ed; padding: 32px; border-radius: 0 0 12px 12px; border: 1px solid #fed7aa;">
        <h2 style="color: #1f2937;">Application Update</h2>
        <p style="color: #4b5563;">Hi {name},</p>
        <p style="color: #4b5563;">Thank you for your interest in selling on Bayti. After reviewing your application, we are unable to approve it at this time.</p>
        <p style="color: #4b5563;">You are welcome to apply again in the future. If you have any questions, please contact us.</p>
        <hr style="border: none; border-top: 1px solid #fed7aa; margin: 24px 0;">
        <p style="color: #9ca3af; font-size: 14px;">Bayti — UAE's Local Products Marketplace</p>
      </div>
    </div>
    """
    return send_email(to, "Bayti Application Update", html)
