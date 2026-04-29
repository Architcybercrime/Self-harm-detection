"""
alerts.py
High-risk alert dispatch via Email (SendGrid) and WhatsApp/SMS (Twilio).
All keys are optional — missing keys silently disable that channel.
"""

import os
import datetime

SENDGRID_KEY    = os.getenv("SENDGRID_API_KEY", "")
SENDGRID_FROM   = os.getenv("SENDGRID_FROM_EMAIL", "alerts@safesignal.app")
TWILIO_SID      = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_TOKEN    = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM     = os.getenv("TWILIO_FROM_NUMBER", "")
TWILIO_WA_FROM  = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")


def _alert_body(username: str, risk_level: str, confidence: float,
                modality: str, text_snippet: str = "") -> str:
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    snippet = f'\n\nText snippet: "{text_snippet[:120]}..."' if text_snippet else ""
    return (
        f"🚨 SafeSignal HIGH-RISK ALERT\n\n"
        f"User:       {username}\n"
        f"Risk level: {risk_level}\n"
        f"Confidence: {confidence:.1%}\n"
        f"Modality:   {modality}\n"
        f"Time:       {ts}"
        f"{snippet}\n\n"
        f"Please review immediately at https://safesignal-api.onrender.com/docs"
    )


def send_email_alert(to_email: str, username: str, risk_level: str,
                     confidence: float, modality: str, text_snippet: str = "") -> bool:
    """Send high-risk alert email via SendGrid. Returns True on success."""
    if not SENDGRID_KEY or not to_email:
        return False
    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail
        sg  = sendgrid.SendGridAPIClient(api_key=SENDGRID_KEY)
        msg = Mail(
            from_email    = SENDGRID_FROM,
            to_emails     = to_email,
            subject       = f"🚨 SafeSignal Alert — HIGH RISK detected for {username}",
            plain_text_content = _alert_body(username, risk_level, confidence,
                                             modality, text_snippet),
        )
        resp = sg.client.mail.send.post(request_body=msg.get())
        return resp.status_code in (200, 202)
    except Exception as e:
        print(f"[alerts] email error: {e}")
        return False


def send_sms_alert(to_number: str, username: str, risk_level: str,
                   confidence: float, modality: str) -> bool:
    """Send high-risk alert SMS via Twilio. Returns True on success."""
    if not TWILIO_SID or not TWILIO_TOKEN or not to_number:
        return False
    try:
        from twilio.rest import Client
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        body   = (f"🚨 SafeSignal: HIGH RISK ({confidence:.0%}) for {username} "
                  f"via {modality}. Check dashboard immediately.")
        client.messages.create(to=to_number, from_=TWILIO_FROM, body=body)
        return True
    except Exception as e:
        print(f"[alerts] SMS error: {e}")
        return False


def send_whatsapp_alert(to_number: str, username: str, risk_level: str,
                        confidence: float, modality: str,
                        text_snippet: str = "") -> bool:
    """Send high-risk alert WhatsApp message via Twilio Sandbox."""
    if not TWILIO_SID or not TWILIO_TOKEN or not to_number:
        return False
    try:
        from twilio.rest import Client
        client   = Client(TWILIO_SID, TWILIO_TOKEN)
        wa_to    = f"whatsapp:{to_number}" if not to_number.startswith("whatsapp:") else to_number
        body     = _alert_body(username, risk_level, confidence, modality, text_snippet)
        client.messages.create(to=wa_to, from_=TWILIO_WA_FROM, body=body)
        return True
    except Exception as e:
        print(f"[alerts] WhatsApp error: {e}")
        return False


def dispatch_high_risk_alert(username: str, confidence: float, modality: str,
                              text_snippet: str = "", profile: dict = None) -> dict:
    """
    Fire all configured alert channels for a high-risk prediction.
    profile: dict with keys alert_email, alert_phone, alert_whatsapp,
             email_alerts, sms_alerts, whatsapp_alerts
    """
    if not profile:
        return {"email": False, "sms": False, "whatsapp": False}

    results = {}

    if profile.get("email_alerts") and profile.get("alert_email"):
        results["email"] = send_email_alert(
            profile["alert_email"], username, "HIGH", confidence, modality, text_snippet)

    if profile.get("sms_alerts") and profile.get("alert_phone"):
        results["sms"] = send_sms_alert(
            profile["alert_phone"], username, "HIGH", confidence, modality)

    if profile.get("whatsapp_alerts") and profile.get("alert_whatsapp"):
        results["whatsapp"] = send_whatsapp_alert(
            profile["alert_whatsapp"], username, "HIGH", confidence, modality, text_snippet)

    return results
