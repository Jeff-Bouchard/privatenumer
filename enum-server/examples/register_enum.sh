#!/bin/bash
# Example: Register ENUM record via Emercoin CLI

# Configuration
PHONE="+1234567890"
SIP_URI="sip:alice@example.com"
FALLBACK_URI="sip:alice-backup@example.com"
DAYS=365

# Convert phone to ENUM domain
# +1234567890 -> 0.9.8.7.6.5.4.3.2.1.e164.arpa
DIGITS=$(echo "$PHONE" | tr -d '+')
REVERSED=$(echo "$DIGITS" | rev | sed 's/./&./g' | sed 's/\.$//')
ENUM_DOMAIN="${REVERSED}.e164.arpa"
NVS_KEY="enum:${ENUM_DOMAIN}"

echo "Phone Number: $PHONE"
echo "ENUM Domain: $ENUM_DOMAIN"
echo "NVS Key: $NVS_KEY"
echo ""

# Build NAPTR value
NAPTR_VALUE="\"!^.*\$!${SIP_URI}!\"|\"!^.*\$!${FALLBACK_URI}!\""

echo "NAPTR Value: $NAPTR_VALUE"
echo ""

# Check if wallet is encrypted
echo "Checking wallet status..."
WALLET_INFO=$(emercoin-cli getinfo 2>&1)

if [[ $? -ne 0 ]]; then
    echo "ERROR: Cannot connect to Emercoin node"
    echo "Make sure emercoind is running"
    exit 1
fi

# Unlock wallet if needed
echo ""
read -sp "Wallet Passphrase (leave empty if not encrypted): " PASSPHRASE
echo ""

if [[ -n "$PASSPHRASE" ]]; then
    echo "Unlocking wallet for 300 seconds..."
    emercoin-cli walletpassphrase "$PASSPHRASE" 300
    
    if [[ $? -ne 0 ]]; then
        echo "ERROR: Failed to unlock wallet"
        exit 1
    fi
fi

# Check if name already exists
echo "Checking if ENUM record already exists..."
EXISTING=$(emercoin-cli name_show "$NVS_KEY" 2>&1)

if [[ $? -eq 0 ]]; then
    echo "Record already exists!"
    echo "$EXISTING"
    echo ""
    read -p "Update existing record? (y/n): " UPDATE
    
    if [[ "$UPDATE" == "y" ]]; then
        echo "Updating record..."
        emercoin-cli name_update "$NVS_KEY" "$NAPTR_VALUE" $DAYS
        
        if [[ $? -eq 0 ]]; then
            echo "SUCCESS: ENUM record updated"
        else
            echo "ERROR: Failed to update record"
            exit 1
        fi
    else
        echo "Aborted"
        exit 0
    fi
else
    # Register new record
    echo "Registering new ENUM record..."
    RESULT=$(emercoin-cli name_new "$NVS_KEY" "$NAPTR_VALUE" $DAYS)
    
    if [[ $? -eq 0 ]]; then
        echo "SUCCESS: ENUM record registered"
        echo ""
        echo "Transaction Details:"
        echo "$RESULT" | jq '.'
        echo ""
        echo "Note: Transaction needs 12 confirmations before it becomes active"
        echo "Check status with: emercoin-cli name_show \"$NVS_KEY\""
    else
        echo "ERROR: Failed to register record"
        echo "$RESULT"
        exit 1
    fi
fi

echo ""
echo "ENUM registration complete!"
echo ""
echo "Test with:"
echo "  curl \"http://localhost:8080/enum/lookup?number=$PHONE\""
