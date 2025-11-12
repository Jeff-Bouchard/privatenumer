# ENUM Backend for Antisip Android App on Raspberry Pi

This project sets up an ENUM (E.164 Number Mapping) backend on a Raspberry Pi with a SIM adapter, integrated with Emercoin core node for DNS/ENUM services.

## Prerequisites

1. Raspberry Pi with Raspberry Pi OS (32-bit or 64-bit)
2. Emercoin Core Node installed and synchronized
3. 3G/4G USB dongle with SIM card
4. Static public IP or dynamic DNS setup

## Installation

1. Install required packages:
   ```bash
   sudo apt update
   sudo apt install -y kamailio kamailio-json kamailio-tls-modules kamailio-utils
   ```

2. Configure Kamailio (see `etc/kamailio/kamailio.cfg`)

3. Set up Emercoin NVS records for ENUM (see `scripts/setup_enum_records.sh`)

4. Configure the SIM adapter (see `scripts/setup_sim_adapter.sh`)

5. Configure Antisip Android app to use your ENUM service

## Configuration

### Kamailio ENUM Configuration
Edit `/etc/kamailio/kamailio.cfg` to include ENUM lookup:

```
# Load ENUM module
loadmodule "enum.so"

# ENUM lookup route
route[ENUM_LOOKUP] {
    if (is_uri_user_e164()) {
        if (enum_query("e164.arpa", "E2U+sip", "")) {
            xlog("ENUM lookup successful for $rU");
            route(RELAY);
            exit;
        }
    }
}
```

### Emercoin NVS Records
Create ENUM records in Emercoin NVS:

```bash
./emercoin-cli name_new dns/e164/1/2/3/4/5/6/7/8/9/0/e164.arpa. "e2u+sip:example.com" "e2u+tel:tel:+1234567890"
```

## Usage

1. Start Kamailio service:
   ```bash
   sudo systemctl start kamailio
   ```

2. Test ENUM lookup:
   ```bash
   kamcmd enum.query 1.2.3.4.5.6.7.8.9.0.e164.arpa
   ```

3. Configure Antisip Android app:
   - Set SIP server to your Raspberry Pi's IP
   - Enable ENUM lookup
   - Set ENUM domain to `e164.arpa`

## Troubleshooting

Check Kamailio logs:
```bash
sudo journalctl -u kamailio -f
```

Check Emercoin debug log:
```bash
tail -f ~/.emercoin/debug.log
```
