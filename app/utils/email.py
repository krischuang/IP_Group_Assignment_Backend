import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.config import settings

_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
</head>
<body style="margin:0;padding:0;background-color:#eef2ff;font-family:Arial,Helvetica,sans-serif;">

  <!-- Header -->
  <div style="background-color:#2563eb;padding:32px 24px;text-align:center;">
    <h1 style="margin:0;color:#ffffff;font-size:2.4em;font-weight:700;letter-spacing:2px;">UTSFE</h1>
  </div>

  <!-- Card -->
  <div style="max-width:620px;margin:36px auto;background:#f8f9fa;border-radius:12px;padding:44px 48px;">

    <h2 style="margin:0 0 20px 0;color:#111827;font-size:1.8em;font-weight:700;">
      Reset Your Password
    </h2>

    <p style="margin:0 0 12px 0;font-size:1.05em;color:#374151;">Hello,</p>

    <p style="margin:0 0 28px 0;font-size:1.05em;color:#374151;line-height:1.6;">
      We received a request to reset the password for your UTSFE account.
      Use the verification code below to continue:
    </p>

    <!-- OTP Box -->
    <div style="border:2px solid #2563eb;border-radius:14px;padding:36px 24px;text-align:center;margin:0 0 20px 0;background:#ffffff;">
      <span style="font-size:3.4em;font-weight:700;color:#2563eb;letter-spacing:0.45em;font-family:'Courier New',Courier,monospace;">
        {spaced_token}
      </span>
    </div>

    <p style="text-align:center;color:#6b7280;font-size:1.05em;margin:0 0 28px 0;">
      Enter this code to reset your password
    </p>

    <!-- Warning box -->
    <div style="border-left:5px solid #f59e0b;background:#fffbeb;border-radius:0 8px 8px 0;padding:16px 20px;margin:0 0 28px 0;">
      <p style="margin:0;font-size:1em;color:#1f2937;line-height:1.5;">
        <strong>Important:</strong> This code will expire in {expire_minutes} minutes for security reasons.
      </p>
    </div>

    <p style="font-size:1em;color:#374151;line-height:1.6;margin:0;">
      If you did not request a password reset, please ignore this email — your account remains safe.
    </p>

  </div>

  <!-- Footer -->
  <p style="text-align:center;color:#9ca3af;font-size:0.85em;padding:0 0 32px 0;">
    &copy; 2026 UTSFE &mdash; Stories, ideas and knowledge, curated.
  </p>

</body>
</html>
"""


async def send_reset_email(to_email: str, token: str) -> None:
    spaced_token = " ".join(list(token))

    html_body = _HTML_TEMPLATE.format(
        spaced_token=spaced_token,
        expire_minutes=settings.reset_token_expire_minutes,
    )

    message = MIMEMultipart("alternative")
    message["From"] = settings.smtp_from
    message["To"] = to_email
    message["Subject"] = "Your UTSFE Password Reset Code"

    plain_body = (
        f"Your UTSFE password reset code is: {token}\n\n"
        f"This code expires in {settings.reset_token_expire_minutes} minutes.\n\n"
        f"If you did not request this, please ignore this email."
    )
    message.attach(MIMEText(plain_body, "plain"))
    message.attach(MIMEText(html_body, "html"))

    await aiosmtplib.send(
        message,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_username,
        password=settings.smtp_password,
        start_tls=True,
    )
