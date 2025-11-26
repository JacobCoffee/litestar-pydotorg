"""Email templates for various user notifications."""

from __future__ import annotations


def get_verification_email_html(username: str, verification_link: str) -> str:
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verify Your Email - Python.org</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background-color: #f8f9fa; border-radius: 8px; padding: 30px; margin: 20px 0;">
        <h1 style="color: #306998; margin-top: 0;">Welcome to Python.org!</h1>
        <p>Hello {username},</p>
        <p>Thank you for creating an account. Please verify your email address by clicking the button below:</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{verification_link}"
               style="background-color: #306998; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                Verify Email Address
            </a>
        </div>
        <p>Or copy and paste this link into your browser:</p>
        <p style="word-break: break-all; color: #666; font-size: 14px;">{verification_link}</p>
        <p style="color: #666; font-size: 14px; margin-top: 30px;">
            This verification link will expire in 24 hours.
        </p>
        <p style="color: #666; font-size: 14px;">
            If you didn't create this account, you can safely ignore this email.
        </p>
    </div>
    <div style="text-align: center; color: #666; font-size: 12px; margin-top: 20px;">
        <p>&copy; Python Software Foundation</p>
    </div>
</body>
</html>
"""


def get_verification_email_text(username: str, verification_link: str) -> str:
    return f"""
Welcome to Python.org!

Hello {username},

Thank you for creating an account. Please verify your email address by clicking the link below:

{verification_link}

This verification link will expire in 24 hours.

If you didn't create this account, you can safely ignore this email.

---
Python Software Foundation
"""


def get_password_reset_email_html(username: str, reset_link: str) -> str:
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reset Your Password - Python.org</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background-color: #f8f9fa; border-radius: 8px; padding: 30px; margin: 20px 0;">
        <h1 style="color: #306998; margin-top: 0;">Password Reset Request</h1>
        <p>Hello {username},</p>
        <p>We received a request to reset your password. Click the button below to create a new password:</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{reset_link}"
               style="background-color: #306998; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                Reset Password
            </a>
        </div>
        <p>Or copy and paste this link into your browser:</p>
        <p style="word-break: break-all; color: #666; font-size: 14px;">{reset_link}</p>
        <p style="color: #666; font-size: 14px; margin-top: 30px;">
            This password reset link will expire in 1 hour.
        </p>
        <p style="color: #d9534f; font-size: 14px; font-weight: bold;">
            If you didn't request a password reset, please ignore this email or contact support if you have concerns.
        </p>
    </div>
    <div style="text-align: center; color: #666; font-size: 12px; margin-top: 20px;">
        <p>&copy; Python Software Foundation</p>
    </div>
</body>
</html>
"""


def get_password_reset_email_text(username: str, reset_link: str) -> str:
    return f"""
Password Reset Request

Hello {username},

We received a request to reset your password. Click the link below to create a new password:

{reset_link}

This password reset link will expire in 1 hour.

If you didn't request a password reset, please ignore this email or contact support if you have concerns.

---
Python Software Foundation
"""
