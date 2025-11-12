#!/usr/bin/env python3
"""
Complete Example: ENUM + SMS Integration for Telegram/2FA
Demonstrates full flow from number registration to SMS delivery
"""

import sys
sys.path.append('..')

from sms_gateway import TelnyxGateway, SMSManager
import json

def example_1_register_number_with_sms():
    """
    Example 1: Register a Telnyx mobile number in Emercoin NVS
    This number will work with Telegram and 2FA services
    """
    print("\n" + "="*60)
    print("Example 1: Register Number with SMS Capability")
    print("="*60)
    
    # Step 1: Buy number from Telnyx (mobile range)
    print("\n1. Buying mobile number from Telnyx...")
    telnyx = TelnyxGateway("YOUR_TELNYX_API_KEY")
    
    # In production, you'd call telnyx.buy_number()
    phone_number = "+14155551234"  # Example number
    print(f"   ✓ Purchased: {phone_number}")
    
    # Step 2: Create ENUM record in Emercoin NVS
    print("\n2. Creating ENUM record in Emercoin NVS...")
    
    enum_record = {
        "voice": "!^.*$!sip:alice@example.com!",
        "sms": {
            "provider": "telnyx",
            "number": phone_number,
            "forward_to": "alice@example.com"
        }
    }
    
    # Convert phone to ENUM domain
    digits = phone_number.strip('+')
    reversed_digits = digits[::-1]
    enum_domain = '.'.join(reversed_digits) + '.e164.arpa'
    nvs_key = f"enum:{enum_domain}"
    
    print(f"   Phone: {phone_number}")
    print(f"   ENUM Domain: {enum_domain}")
    print(f"   NVS Key: {nvs_key}")
    
    # Emercoin CLI command (run this manually)
    cmd = f"""
emercoin-cli name_new \\
  "{nvs_key}" \\
  '{json.dumps(enum_record)}' \\
  365
"""
    print(f"\n   Run this command:")
    print(cmd)
    
    print("\n   ✓ ENUM record ready for registration")


def example_2_telegram_registration():
    """
    Example 2: User registers on Telegram with your number
    Flow: Telegram → Telnyx → Your webhook → User notification
    """
    print("\n" + "="*60)
    print("Example 2: Telegram Registration Flow")
    print("="*60)
    
    phone_number = "+14155551234"
    
    print(f"\n1. User opens Telegram and enters: {phone_number}")
    print("2. Telegram sends SMS code via carrier network")
    print("3. Telnyx receives SMS (because you own the number)")
    print("4. Telnyx posts to your webhook: /sms/webhook/telnyx")
    
    # Simulated webhook payload from Telnyx
    webhook_payload = {
        "data": {
            "event_type": "message.received",
            "payload": {
                "from": {
                    "phone_number": "+12223334444"  # Telegram's SMS gateway
                },
                "to": [{
                    "phone_number": phone_number
                }],
                "text": "Telegram code: 12345",
                "received_at": "2024-01-15T10:30:00Z"
            }
        }
    }
    
    print("\n5. Webhook receives payload:")
    print(json.dumps(webhook_payload, indent=2))
    
    # Your webhook processing
    sms_text = webhook_payload["data"]["payload"]["text"]
    code = sms_text.split(": ")[1] if ": " in sms_text else "12345"
    
    print(f"\n6. Extracted verification code: {code}")
    print("7. Forward code to user via:")
    print("   - Email: alice@example.com")
    print("   - Push notification")
    print("   - Web dashboard")
    print("\n8. User enters code in Telegram")
    print("   ✓ Account verified!")


def example_3_send_2fa_code():
    """
    Example 3: Your service sends 2FA code via SMS
    """
    print("\n" + "="*60)
    print("Example 3: Send 2FA Code to User")
    print("="*60)
    
    # Initialize SMS gateway
    telnyx = TelnyxGateway("YOUR_TELNYX_API_KEY")
    
    # User trying to log in
    user_phone = "+14155551234"
    verification_code = "987654"
    
    print(f"\n1. User requests login to your service")
    print(f"2. Generate 2FA code: {verification_code}")
    print(f"3. Send SMS to user's phone: {user_phone}")
    
    # Send SMS
    result = telnyx.send_sms(
        from_number="+14155551234",  # Your Telnyx number
        to_number=user_phone,
        message=f"Your verification code is: {verification_code}"
    )
    
    if result.get("success"):
        print(f"\n   ✓ SMS sent successfully")
        print(f"   Message ID: {result.get('message_id')}")
        print(f"   Status: {result.get('status')}")
    else:
        print(f"\n   ✗ SMS failed: {result.get('error')}")
    
    print("\n4. User receives SMS on their phone")
    print("5. User enters code on your website")
    print("   ✓ Login successful!")


def example_4_banking_app_verification():
    """
    Example 4: Bank app verifies phone number (like Chase, Wells Fargo)
    """
    print("\n" + "="*60)
    print("Example 4: Banking App Phone Verification")
    print("="*60)
    
    phone_number = "+14155551234"
    
    print(f"\n1. User enters phone in banking app: {phone_number}")
    print("2. Bank performs HLR lookup:")
    print("   - Queries carrier database")
    print("   - Checks if number is mobile or VoIP")
    
    # Simulated HLR response
    hlr_response = {
        "number": phone_number,
        "number_type": "mobile",  # ← This is key!
        "carrier": "T-Mobile USA",
        "country": "US",
        "status": "active"
    }
    
    print("\n3. HLR Response:")
    print(json.dumps(hlr_response, indent=2))
    
    if hlr_response["number_type"] == "mobile":
        print("\n   ✓ Number accepted (appears as mobile)")
        print("4. Bank sends SMS verification code")
        print("5. User receives code via your SMS gateway")
        print("6. User enters code in app")
        print("   ✓ Phone verified!")
    else:
        print("\n   ✗ Number rejected (detected as VoIP)")


def example_5_cost_breakdown():
    """
    Example 5: Monthly cost breakdown for 100 users
    """
    print("\n" + "="*60)
    print("Example 5: Cost Breakdown (100 Users)")
    print("="*60)
    
    users = 100
    sms_per_user_per_month = 20  # 2FA codes, notifications, etc.
    
    # Telnyx pricing
    telnyx_number_cost = 2.00
    telnyx_sms_cost = 0.004
    
    telnyx_monthly = (users * telnyx_number_cost) + \
                     (users * sms_per_user_per_month * telnyx_sms_cost)
    
    # Bandwidth pricing
    bandwidth_number_cost = 0.40
    bandwidth_sms_cost = 0.0035
    
    bandwidth_monthly = (users * bandwidth_number_cost) + \
                       (users * sms_per_user_per_month * bandwidth_sms_cost)
    
    # Android DIY (10 phones, 10 SIMs unlimited)
    android_phones = 10
    android_phone_cost = 50  # per phone
    android_sim_cost = 20  # per month
    
    android_setup = android_phones * android_phone_cost
    android_monthly = android_phones * android_sim_cost
    
    print(f"\nTelnyx (Best for Telegram):")
    print(f"  Numbers: {users} × ${telnyx_number_cost} = ${users * telnyx_number_cost}")
    print(f"  SMS: {users * sms_per_user_per_month} × ${telnyx_sms_cost} = ${users * sms_per_user_per_month * telnyx_sms_cost}")
    print(f"  Total: ${telnyx_monthly:.2f}/month")
    
    print(f"\nBandwidth (Cheapest):")
    print(f"  Numbers: {users} × ${bandwidth_number_cost} = ${users * bandwidth_number_cost}")
    print(f"  SMS: {users * sms_per_user_per_month} × ${bandwidth_sms_cost} = ${users * sms_per_user_per_month * bandwidth_sms_cost}")
    print(f"  Total: ${bandwidth_monthly:.2f}/month")
    
    print(f"\nAndroid DIY (Fixed Cost):")
    print(f"  Phones: {android_phones} × ${android_phone_cost} = ${android_setup} (one-time)")
    print(f"  SIMs: {android_phones} × ${android_sim_cost} = ${android_monthly}/month")
    print(f"  Total: ${android_monthly}/month + ${android_setup} setup")
    
    print(f"\n💡 Recommendation:")
    print(f"  For {users} users: Use Bandwidth.com (${bandwidth_monthly:.2f}/month)")


def example_6_complete_integration():
    """
    Example 6: Complete user journey from signup to 2FA
    """
    print("\n" + "="*60)
    print("Example 6: Complete User Journey")
    print("="*60)
    
    print("\n📱 User Journey:")
    print("\n1. USER SIGNUP")
    print("   - User visits your website")
    print("   - Clicks 'Get Started'")
    print("   - Chooses phone number from pool")
    print("   - Downloads your app (QR code config)")
    
    print("\n2. NUMBER ACTIVATION")
    print("   - User scans QR code")
    print("   - App configures:")
    print("     * SIP account: user123@yourservice.com")
    print("     * ENUM server: enum.yourservice.com")
    print("     * SMS webhook: api.yourservice.com/sms")
    print("   - User's phone number: +14155551234")
    
    print("\n3. TELEGRAM REGISTRATION")
    print("   - User opens Telegram")
    print("   - Enters: +14155551234")
    print("   - Telegram sends SMS → Telnyx → Your webhook")
    print("   - Your app shows notification: 'Code: 12345'")
    print("   - User enters code")
    print("   - ✓ Telegram account created")
    
    print("\n4. BANKING APP SETUP")
    print("   - User opens Chase app")
    print("   - Adds +14155551234 for 2FA")
    print("   - Bank sends verification SMS")
    print("   - Your app receives SMS, shows code")
    print("   - User verifies")
    print("   - ✓ Bank account secured with 2FA")
    
    print("\n5. DAILY USAGE")
    print("   - User makes VoIP calls: Direct P2P via SIP")
    print("   - User receives 2FA codes: Via your SMS gateway")
    print("   - User sends SMS: Via your SMS gateway")
    print("   - Cost to user: $5-10/month (vs $50+ carrier)")
    
    print("\n6. BEHIND THE SCENES")
    print("   - Voice: ENUM → SIP URI → Direct call")
    print("   - SMS: Telnyx API → Your webhook → User notification")
    print("   - All metadata in Emercoin blockchain")
    print("   - No carrier control, full privacy")


def main():
    """Run all examples"""
    examples = [
        ("Register Number with SMS", example_1_register_number_with_sms),
        ("Telegram Registration Flow", example_2_telegram_registration),
        ("Send 2FA Code", example_3_send_2fa_code),
        ("Banking App Verification", example_4_banking_app_verification),
        ("Cost Breakdown", example_5_cost_breakdown),
        ("Complete User Journey", example_6_complete_integration),
    ]
    
    print("\n" + "="*60)
    print("ENUM + SMS Integration Examples")
    print("Telegram-Compatible Phone Numbers with Emercoin NVS")
    print("="*60)
    
    for i, (name, func) in enumerate(examples, 1):
        print(f"\n[{i}/{len(examples)}] {name}")
        input("Press Enter to continue...")
        func()
    
    print("\n" + "="*60)
    print("All Examples Complete!")
    print("="*60)
    print("\nNext Steps:")
    print("1. Sign up for Telnyx: https://portal.telnyx.com")
    print("2. Get API key and buy a mobile number")
    print("3. Update sms_gateway.py with your credentials")
    print("4. Register number in Emercoin NVS")
    print("5. Test with Telegram registration")
    print("\nDocumentation: See SMS_SETUP.md for detailed guide")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
