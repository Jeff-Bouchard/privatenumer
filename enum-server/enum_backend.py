#!/usr/bin/env python3
"""
ENUM Backend for Antisip using Emercoin NVS
RFC 6116-based ENUM implementation with simplified NAPTR format for Emercoin NVS
"""

import subprocess
import json
import re
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import logging
from typing import Optional, Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for Antisip requests

# Emercoin Configuration
EMC_CLI_PATH = "/usr/local/bin/emercoin-cli"
EMC_DATADIR = "/home/pi/.emercoin"
ENUM_PREFIX = "enum:"

class EmercoinNVS:
    """Interface to Emercoin Name-Value Storage"""
    
    @staticmethod
    def execute_rpc(method: str, params: List = None) -> Optional[Dict]:
        """Execute Emercoin RPC command"""
        try:
            cmd = [EMC_CLI_PATH, f"-datadir={EMC_DATADIR}", method]
            if params:
                cmd.extend([str(p) for p in params])
            
            logger.debug(f"Executing: {' '.join(cmd)}")
            result = subprocess.check_output(cmd, stderr=subprocess.PIPE, timeout=10)
            
            # Parse JSON response
            output = result.decode('utf-8').strip()
            if output:
                return json.loads(output)
            return None
            
        except subprocess.CalledProcessError as e:
            logger.error(f"RPC error: {e.stderr.decode('utf-8')}")
            return None
        except subprocess.TimeoutExpired:
            logger.error(f"RPC timeout for method {method}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None
    
    @classmethod
    def name_show(cls, name: str) -> Optional[Dict]:
        """Query NVS record by name"""
        result = cls.execute_rpc("name_show", [name])
        return result
    
    @classmethod
    def name_filter(cls, prefix: str, max_results: int = 100) -> Optional[List[Dict]]:
        """Filter NVS records by prefix"""
        result = cls.execute_rpc("name_filter", [prefix, max_results])
        return result


class ENUMResolver:
    """ENUM resolution logic"""
    
    @staticmethod
    def e164_to_enum(phone_number: str) -> str:
        """
        Convert E.164 phone number to ENUM domain
        Example: +1234567890 -> 0.9.8.7.6.5.4.3.2.1.e164.arpa
        """
        # Strip all non-digits
        digits = re.sub(r'\D', '', phone_number)
        
        # Reverse and add dots
        reversed_digits = digits[::-1]
        enum_domain = '.'.join(reversed_digits) + '.e164.arpa'
        
        return enum_domain
    
    @staticmethod
    def parse_naptr_record(naptr_value: str) -> List[Dict]:
        """
        Parse NAPTR record format
        Example: "!^.*$!sip:user@domain.com!"|"!^.*$!sip:backup@domain.com!"
        """
        records = []
        
        # Split by pipe for multiple entries
        entries = naptr_value.split('|')
        
        for entry in entries:
            entry = entry.strip().strip('"')
            
            # Parse NAPTR format: !pattern!replacement!flags
            match = re.match(r'!([^!]*)!([^!]*)!([^!]*)?', entry)
            if match:
                pattern, replacement, flags = match.groups()
                records.append({
                    'pattern': pattern or '^.*$',
                    'replacement': replacement,
                    'flags': flags or 'u',
                    'order': len(records),  # Priority based on order
                    'preference': 10
                })
        
        return records
    
    @classmethod
    def resolve_enum(cls, phone_number: str) -> Optional[Dict]:
        """
        Resolve phone number to SIP URI via Emercoin NVS
        """
        # Convert to ENUM format
        enum_domain = cls.e164_to_enum(phone_number)
        nvs_key = f"{ENUM_PREFIX}{enum_domain}"
        
        logger.info(f"Resolving {phone_number} -> {nvs_key}")
        
        # Query Emercoin NVS
        nvs_record = EmercoinNVS.name_show(nvs_key)
        
        if not nvs_record:
            logger.warning(f"No NVS record found for {nvs_key}")
            return None
        
        # Parse NAPTR records
        naptr_value = nvs_record.get('value', '')
        naptr_records = cls.parse_naptr_record(naptr_value)
        
        if not naptr_records:
            logger.warning(f"No valid NAPTR records in {naptr_value}")
            return None
        
        return {
            'phone_number': phone_number,
            'enum_domain': enum_domain,
            'naptr_records': naptr_records,
            'expires_in': nvs_record.get('expires_in', 0),
            'address': nvs_record.get('address', ''),
            'nvs_key': nvs_key
        }


# API Endpoints

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Test Emercoin connection
        info = EmercoinNVS.execute_rpc("getinfo")
        if info:
            return jsonify({
                'status': 'healthy',
                'emercoin_connected': True,
                'blocks': info.get('blocks', 0),
                'version': info.get('version', 'unknown')
            }), 200
        else:
            return jsonify({
                'status': 'degraded',
                'emercoin_connected': False
            }), 503
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/enum/lookup', methods=['GET'])
def enum_lookup():
    """
    ENUM lookup endpoint for Antisip
    Query parameter: number (E.164 format, e.g., +1234567890)
    """
    phone_number = request.args.get('number')
    
    if not phone_number:
        return jsonify({
            'error': 'Missing required parameter: number'
        }), 400
    
    # Resolve ENUM
    result = ENUMResolver.resolve_enum(phone_number)
    
    if not result:
        return jsonify({
            'status': 'not_found',
            'phone_number': phone_number
        }), 404
    
    # Extract primary SIP URI
    primary_uri = result['naptr_records'][0]['replacement'] if result['naptr_records'] else None
    
    return jsonify({
        'status': 'success',
        'phone_number': result['phone_number'],
        'sip_uri': primary_uri,
        'naptr_records': result['naptr_records'],
        'enum_domain': result['enum_domain'],
        'expires_in': result['expires_in'],
        'owner_address': result['address']
    }), 200


@app.route('/enum/register', methods=['POST'])
def enum_register():
    """
    Register new ENUM record in Emercoin NVS
    Body: {
        "phone_number": "+1234567890",
        "sip_uri": "sip:user@domain.com",
        "fallback_uris": ["sip:backup@domain.com"]  # optional
    }
    """
    data = request.get_json()
    
    if not data or 'phone_number' not in data or 'sip_uri' not in data:
        return jsonify({
            'error': 'Missing required fields: phone_number, sip_uri'
        }), 400
    
    phone_number = data['phone_number']
    sip_uri = data['sip_uri']
    fallback_uris = data.get('fallback_uris', [])
    
    # Build NAPTR value
    naptr_entries = [f'"!^.*$!{sip_uri}!"']
    for uri in fallback_uris:
        naptr_entries.append(f'"!^.*$!{uri}!"')
    
    naptr_value = '|'.join(naptr_entries)
    
    # Generate NVS key
    enum_domain = ENUMResolver.e164_to_enum(phone_number)
    nvs_key = f"{ENUM_PREFIX}{enum_domain}"
    
    logger.info(f"Registering {nvs_key} = {naptr_value}")
    
    # Register in NVS (requires wallet to be unlocked)
    try:
        result = EmercoinNVS.execute_rpc("name_new", [nvs_key, naptr_value, 365])
        
        if result:
            return jsonify({
                'status': 'success',
                'nvs_key': nvs_key,
                'phone_number': phone_number,
                'enum_domain': enum_domain,
                'txid': result.get('txid', ''),
                'message': 'ENUM record registered (requires confirmation)'
            }), 201
        else:
            return jsonify({
                'error': 'Failed to register ENUM record'
            }), 500
            
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({
            'error': f'Registration failed: {str(e)}'
        }), 500


@app.route('/enum/list', methods=['GET'])
def enum_list():
    """List all ENUM records in NVS"""
    try:
        records = EmercoinNVS.name_filter(ENUM_PREFIX, 1000)
        
        if records is None:
            return jsonify({
                'error': 'Failed to query NVS'
            }), 500
        
        # Parse records
        parsed_records = []
        for record in records:
            name = record.get('name', '')
            value = record.get('value', '')
            
            # Extract phone number from ENUM domain
            enum_domain = name.replace(ENUM_PREFIX, '')
            digits = enum_domain.replace('.e164.arpa', '').replace('.', '')
            phone_number = '+' + digits[::-1]
            
            # Parse NAPTR
            naptr_records = ENUMResolver.parse_naptr_record(value)
            primary_uri = naptr_records[0]['replacement'] if naptr_records else None
            
            parsed_records.append({
                'phone_number': phone_number,
                'sip_uri': primary_uri,
                'nvs_key': name,
                'expires_in': record.get('expires_in', 0)
            })
        
        return jsonify({
            'status': 'success',
            'count': len(parsed_records),
            'records': parsed_records
        }), 200
        
    except Exception as e:
        logger.error(f"List error: {e}")
        return jsonify({
            'error': str(e)
        }), 500


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='ENUM Backend Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', default=8080, type=int, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--emc-cli', default=EMC_CLI_PATH, help='Path to emercoin-cli')
    parser.add_argument('--emc-datadir', default=EMC_DATADIR, help='Emercoin data directory')
    
    args = parser.parse_args()
    
    # Update configuration
    EMC_CLI_PATH = args.emc_cli
    EMC_DATADIR = args.emc_datadir
    
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    logger.info(f"Starting ENUM Backend Server on {args.host}:{args.port}")
    logger.info(f"Emercoin CLI: {EMC_CLI_PATH}")
    logger.info(f"Emercoin Datadir: {EMC_DATADIR}")
    
    # Run server
    app.run(host=args.host, port=args.port, debug=args.debug)
