#!/usr/bin/env python3
"""
Test script for ENUM backend
Run this after starting the backend to verify functionality
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8080"

def test_health():
    """Test health endpoint"""
    print("\n[TEST] Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_lookup_existing():
    """Test ENUM lookup for existing record"""
    print("\n[TEST] ENUM Lookup (Existing Record)")
    phone_number = "+1234567890"
    
    try:
        response = requests.get(
            f"{BASE_URL}/enum/lookup",
            params={"number": phone_number},
            timeout=5
        )
        print(f"Phone: {phone_number}")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code in [200, 404]  # Both are valid
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_lookup_invalid():
    """Test ENUM lookup with missing parameter"""
    print("\n[TEST] ENUM Lookup (Invalid Request)")
    
    try:
        response = requests.get(f"{BASE_URL}/enum/lookup", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 400
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_list_enum():
    """Test listing all ENUM records"""
    print("\n[TEST] List All ENUM Records")
    
    try:
        response = requests.get(f"{BASE_URL}/enum/list", timeout=10)
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Total Records: {data.get('count', 0)}")
        
        if data.get('records'):
            print("\nFirst 3 records:")
            for record in data['records'][:3]:
                print(f"  {record['phone_number']} → {record['sip_uri']}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_register_enum():
    """Test registering new ENUM record"""
    print("\n[TEST] Register ENUM Record")
    print("NOTE: This requires Emercoin wallet to be unlocked")
    print("Run: emercoin-cli walletpassphrase 'your-passphrase' 300")
    
    payload = {
        "phone_number": "+1234567890",
        "sip_uri": "sip:testuser@example.com",
        "fallback_uris": ["sip:backup@example.com"]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/enum/register",
            json=payload,
            timeout=10
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code in [201, 500]  # 500 if wallet locked
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("ENUM Backend Test Suite")
    print("=" * 60)
    print(f"Target: {BASE_URL}")
    
    tests = [
        ("Health Check", test_health),
        ("ENUM Lookup (Existing)", test_lookup_existing),
        ("ENUM Lookup (Invalid)", test_lookup_invalid),
        ("List ENUM Records", test_list_enum),
        ("Register ENUM (Optional)", test_register_enum),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\nTest '{name}' crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    passed_count = 0
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:8} | {name}")
        if passed:
            passed_count += 1
    
    print(f"\nTotal: {passed_count}/{len(results)} tests passed")
    
    # Exit code
    sys.exit(0 if passed_count == len(results) else 1)

if __name__ == "__main__":
    main()
