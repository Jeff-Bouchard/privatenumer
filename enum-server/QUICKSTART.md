# ENUM Backend - Quick Reference Card

## Installation (One Command)

```bash
sudo ./setup.sh
```

## Essential Commands

### Service Management
```bash
sudo systemctl status enum-backend    # Check status
sudo systemctl start enum-backend     # Start
sudo systemctl stop enum-backend      # Stop
sudo systemctl restart enum-backend   # Restart
journalctl -u enum-backend -f         # View logs
```

### Emercoin Operations
```bash
emercoin-cli getinfo                  # Node status
emercoin-cli name_show "enum:..."     # Query record
emercoin-cli walletpassphrase "pass" 300  # Unlock wallet
```

### Register ENUM Record
```bash
# Format: +1234567890 -> enum:0.9.8.7.6.5.4.3.2.1.e164.arpa
emercoin-cli name_new \
  "enum:0.9.8.7.6.5.4.3.2.1.e164.arpa" \
  '"!^.*$!sip:user@domain.com!"' \
  365
```

### Test Endpoints
```bash
curl http://localhost:8080/health
curl "http://localhost:8080/enum/lookup?number=%2B1234567890"
curl http://localhost:8080/enum/list
```

## Antisip Configuration

**Settings → Network → ENUM**
- ENUM Server: `http://YOUR-PI-IP:8080/enum/lookup?number=`
- ENUM Domain: `e164.arpa`
- Enable ENUM: ✓

## File Locations

| Item | Path |
|------|------|
| Backend Script | `/home/pi/enum-server/enum_backend.py` |
| Service File | `/etc/systemd/system/enum-backend.service` |
| Logs | `journalctl -u enum-backend` |
| Emercoin Config | `~/.emercoin/emercoin.conf` |
| Emercoin Wallet | `~/.emercoin/wallet.dat` |

## Common Issues

### Port 8080 in Use
```bash
sudo ss -tlnp | grep 8080
sudo kill <PID>
```

### Emercoin Not Synced
```bash
emercoin-cli getinfo | grep blocks
# Wait for sync to complete
```

### Health Check Fails
```bash
# Check if Emercoin is running
systemctl status emercoin
# Check backend logs
journalctl -u enum-backend -n 50
```

## NAPTR Format Quick Reference

| Use Case | NAPTR Value |
|----------|-------------|
| Single SIP URI | `"!^.*$!sip:user@domain.com!"` |
| Primary + Backup | `"!^.*$!sip:primary@domain.com!\|!^.*$!sip:backup@domain.com!"` |
| Voice Only | `"!^.*$!sip:user@domain.com!u"` |
| Video Call | `"!^.*$!sip:user@domain.com!v"` |

## E.164 to ENUM Conversion

**Phone**: `+1234567890`
↓
**Reversed**: `0987654321`
↓
**Dotted**: `0.9.8.7.6.5.4.3.2.1`
↓
**ENUM Domain**: `0.9.8.7.6.5.4.3.2.1.e164.arpa`
↓
**NVS Key**: `enum:0.9.8.7.6.5.4.3.2.1.e164.arpa`

## API Quick Reference

### GET /health
Returns: Service health and Emercoin connection status

### GET /enum/lookup?number=+1234567890
Returns: SIP URI and NAPTR records for phone number

### POST /enum/register
Body: `{"phone_number": "+123...", "sip_uri": "sip:..."}`
Returns: Transaction ID (requires unlocked wallet)

### GET /enum/list
Returns: All ENUM records in NVS

## Security Checklist

- [ ] Emercoin wallet encrypted
- [ ] RPC limited to localhost (emercoin.conf: `rpcallowip=127.0.0.1`)
- [ ] Firewall configured (ufw)
- [ ] SSL/TLS for public access
- [ ] Regular wallet backups
- [ ] Strong RPC credentials

## Performance Tips

1. **Increase Emercoin cache**: `dbcache=1024` in emercoin.conf
2. **Add Redis caching**: Install redis + flask-caching
3. **Use Gunicorn**: `gunicorn -w 4 enum_backend:app`
4. **SSD instead of SD card** for better I/O

## Backup Commands

```bash
# Backup wallet
emercoin-cli backupwallet ~/backup-$(date +%F).dat

# Backup service config
sudo cp /etc/systemd/system/enum-backend.service ~/backup/

# Backup backend
tar -czf ~/backup/enum-server-$(date +%F).tar.gz /home/pi/enum-server
```

## Cost Summary

- **Hardware**: $80 (one-time)
- **Power**: $0.26/month
- **ENUM Records**: ~$0.10 per number per year
- **Domain (optional)**: $10-15/year

## Support

- Full Documentation: `README.md`
- Deployment Guide: `DEPLOYMENT.md`
- Test Suite: `python3 test_enum.py`
