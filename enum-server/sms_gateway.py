#!/usr/bin/env python3
"""
SMS Gateway Integration for ENUM Backend
Supports Telnyx, Bandwidth, and custom mobile gateways
"""

import requests
import json
import logging
from typing import Optional, Dict, List
from flask import Flask, request, jsonify
from datetime import datetime

logger = logging.getLogger(__name__)

# Configuration
TELNYX_API_KEY = "YOUR_TELNYX_API_KEY"
TELNYX_API_BASE = "https://api.telnyx.com/v2"
BANDWIDTH_API_USER = "YOUR_BANDWIDTH_USER"
BANDWIDTH_API_TOKEN = "YOUR_BANDWIDTH_TOKEN"
BANDWIDTH_API_BASE = "https://messaging.bandwidth.com/api/v2"

class SMSGateway:
    """Base SMS gateway interface"""
    
    def send_sms(self, from_number: str, to_number: str, message: str) -> Dict:
        raise NotImplementedError
    
    def get_sms_status(self, message_id: str) -> Dict:
        raise NotImplementedError


class TelnyxGateway(SMSGateway):
    """Telnyx SMS gateway (real mobile numbers)"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def send_sms(self, from_number: str, to_number: str, message: str) -> Dict:
        """Send SMS via Telnyx"""
        url = f"{TELNYX_API_BASE}/messages"
        
        payload = {
            "from": from_number,
            "to": to_number,
            "text": message,
            "messaging_profile_id": "YOUR_MESSAGING_PROFILE_ID"
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            return {
                "success": True,
                "message_id": result["data"]["id"],
                "status": result["data"]["to"][0]["status"],
                "provider": "telnyx"
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Telnyx SMS error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_sms_status(self, message_id: str) -> Dict:
        """Get SMS delivery status"""
        url = f"{TELNYX_API_BASE}/messages/{message_id}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            return {
                "success": True,
                "status": result["data"]["to"][0]["status"],
                "provider": "telnyx"
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Telnyx status error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def buy_number(self, area_code: str = None) -> Dict:
        """Purchase a mobile number from Telnyx"""
        url = f"{TELNYX_API_BASE}/available_phone_numbers"
        
        params = {
            "filter[features]": "sms,mms,voice",
            "filter[limit]": 10
        }
        
        if area_code:
            params["filter[national_destination_code]"] = area_code
        
        try:
            # Search available numbers
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            
            available = response.json()["data"]
            if not available:
                return {"success": False, "error": "No numbers available"}
            
            # Buy first available
            phone_number = available[0]["phone_number"]
            
            purchase_url = f"{TELNYX_API_BASE}/phone_numbers"
            purchase_payload = {
                "phone_number": phone_number
            }
            
            purchase_response = requests.post(
                purchase_url,
                headers=self.headers,
                json=purchase_payload,
                timeout=10
            )
            purchase_response.raise_for_status()
            
            return {
                "success": True,
                "phone_number": phone_number,
                "provider": "telnyx"
            }
        except Exception as e:
            logger.error(f"Telnyx number purchase error: {e}")
            return {"success": False, "error": str(e)}


class BandwidthGateway(SMSGateway):
    """Bandwidth.com SMS gateway (tier-1 carrier)"""
    
    def __init__(self, user_id: str, api_token: str, account_id: str):
        self.user_id = user_id
        self.api_token = api_token
        self.account_id = account_id
        self.auth = (user_id, api_token)
    
    def send_sms(self, from_number: str, to_number: str, message: str) -> Dict:
        """Send SMS via Bandwidth"""
        url = f"{BANDWIDTH_API_BASE}/users/{self.account_id}/messages"
        
        payload = {
            "from": from_number,
            "to": [to_number],
            "text": message,
            "applicationId": "YOUR_APP_ID"
        }
        
        try:
            response = requests.post(url, auth=self.auth, json=payload, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            return {
                "success": True,
                "message_id": result["id"],
                "provider": "bandwidth"
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Bandwidth SMS error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_sms_status(self, message_id: str) -> Dict:
        """Get SMS delivery status"""
        # Bandwidth uses webhooks for status updates
        return {
            "success": True,
            "status": "check_webhook",
            "provider": "bandwidth"
        }


class AndroidSMSGateway(SMSGateway):
    """Forward SMS via Android device with real SIM"""
    
    def __init__(self, gateway_url: str, api_key: str):
        self.gateway_url = gateway_url
        self.api_key = api_key
    
    def send_sms(self, from_number: str, to_number: str, message: str) -> Dict:
        """
        Send SMS via Android SMS Gateway app
        https://github.com/capcom6/android-sms-gateway
        """
        url = f"{self.gateway_url}/message"
        
        payload = {
            "message": message,
            "phoneNumbers": [to_number]
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            return {
                "success": True,
                "message_id": result.get("id", "unknown"),
                "provider": "android_gateway"
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Android gateway SMS error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_sms_status(self, message_id: str) -> Dict:
        """Get SMS status from Android gateway"""
        url = f"{self.gateway_url}/message/{message_id}"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            return {
                "success": True,
                "status": result.get("state", "unknown"),
                "provider": "android_gateway"
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }


class SMSManager:
    """Manage SMS across multiple gateways"""
    
    def __init__(self):
        self.gateways = {}
    
    def add_gateway(self, name: str, gateway: SMSGateway):
        """Register SMS gateway"""
        self.gateways[name] = gateway
    
    def send_sms(self, from_number: str, to_number: str, message: str, 
                 preferred_gateway: str = None) -> Dict:
        """Send SMS via specified or default gateway"""
        
        if preferred_gateway and preferred_gateway in self.gateways:
            gateway = self.gateways[preferred_gateway]
        elif self.gateways:
            gateway = list(self.gateways.values())[0]
        else:
            return {
                "success": False,
                "error": "No SMS gateway configured"
            }
        
        return gateway.send_sms(from_number, to_number, message)
    
    def receive_sms_webhook(self, payload: Dict, provider: str) -> Dict:
        """Process incoming SMS webhook"""
        
        if provider == "telnyx":
            return self._process_telnyx_webhook(payload)
        elif provider == "bandwidth":
            return self._process_bandwidth_webhook(payload)
        elif provider == "android":
            return self._process_android_webhook(payload)
        else:
            return {
                "success": False,
                "error": f"Unknown provider: {provider}"
            }
    
    def _process_telnyx_webhook(self, payload: Dict) -> Dict:
        """Process Telnyx incoming SMS webhook"""
        try:
            data = payload["data"]["payload"]
            
            return {
                "success": True,
                "from": data["from"]["phone_number"],
                "to": data["to"][0]["phone_number"],
                "message": data["text"],
                "timestamp": data["received_at"],
                "provider": "telnyx"
            }
        except KeyError as e:
            logger.error(f"Telnyx webhook parse error: {e}")
            return {"success": False, "error": "Invalid webhook format"}
    
    def _process_bandwidth_webhook(self, payload: Dict) -> Dict:
        """Process Bandwidth incoming SMS webhook"""
        try:
            return {
                "success": True,
                "from": payload["message"]["from"],
                "to": payload["message"]["to"][0],
                "message": payload["message"]["text"],
                "timestamp": payload["message"]["time"],
                "provider": "bandwidth"
            }
        except KeyError as e:
            logger.error(f"Bandwidth webhook parse error: {e}")
            return {"success": False, "error": "Invalid webhook format"}
    
    def _process_android_webhook(self, payload: Dict) -> Dict:
        """Process Android SMS Gateway webhook"""
        try:
            return {
                "success": True,
                "from": payload["phoneNumber"],
                "to": "local_number",  # Android gateway doesn't provide "to"
                "message": payload["message"],
                "timestamp": payload["receivedAt"],
                "provider": "android"
            }
        except KeyError as e:
            logger.error(f"Android webhook parse error: {e}")
            return {"success": False, "error": "Invalid webhook format"}


# Flask routes for SMS integration
app = Flask(__name__)
sms_manager = SMSManager()

# Initialize gateways (configure with your credentials)
# telnyx_gw = TelnyxGateway(TELNYX_API_KEY)
# sms_manager.add_gateway("telnyx", telnyx_gw)

@app.route('/sms/send', methods=['POST'])
def send_sms():
    """
    Send SMS via configured gateway
    Body: {
        "from": "+1234567890",
        "to": "+0987654321",
        "message": "Your code is 123456",
        "gateway": "telnyx"  # optional
    }
    """
    data = request.get_json()
    
    if not data or not all(k in data for k in ["from", "to", "message"]):
        return jsonify({
            "error": "Missing required fields: from, to, message"
        }), 400
    
    result = sms_manager.send_sms(
        data["from"],
        data["to"],
        data["message"],
        data.get("gateway")
    )
    
    if result["success"]:
        return jsonify(result), 200
    else:
        return jsonify(result), 500


@app.route('/sms/webhook/<provider>', methods=['POST'])
def receive_sms_webhook(provider: str):
    """
    Receive incoming SMS from provider webhook
    Configure in provider dashboard:
    - Telnyx: https://your-domain.com/sms/webhook/telnyx
    - Bandwidth: https://your-domain.com/sms/webhook/bandwidth
    - Android: https://your-domain.com/sms/webhook/android
    """
    payload = request.get_json()
    
    result = sms_manager.receive_sms_webhook(payload, provider)
    
    if result["success"]:
        # Forward to application logic (e.g., store in database, notify user)
        logger.info(f"SMS received from {result['from']}: {result['message']}")
        
        # TODO: Integrate with your application
        # - Store in database
        # - Send to user's connected devices
        # - Trigger notifications
        
        return jsonify({"status": "received"}), 200
    else:
        return jsonify(result), 400


@app.route('/sms/status/<message_id>', methods=['GET'])
def get_sms_status(message_id: str):
    """Get SMS delivery status"""
    gateway_name = request.args.get('gateway', 'telnyx')
    
    if gateway_name not in sms_manager.gateways:
        return jsonify({
            "error": f"Gateway {gateway_name} not found"
        }), 404
    
    gateway = sms_manager.gateways[gateway_name]
    result = gateway.get_sms_status(message_id)
    
    return jsonify(result), 200 if result["success"] else 500


if __name__ == "__main__":
    # Example usage
    print("SMS Gateway Integration Example")
    print("=" * 50)
    
    # Initialize Telnyx gateway
    if TELNYX_API_KEY != "YOUR_TELNYX_API_KEY":
        telnyx = TelnyxGateway(TELNYX_API_KEY)
        sms_manager.add_gateway("telnyx", telnyx)
        print("✓ Telnyx gateway configured")
    
    # Start Flask server
    app.run(host='0.0.0.0', port=8081, debug=True)
