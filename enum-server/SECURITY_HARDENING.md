# Security Hardening Guide

Advanced security configurations for production ENUM backend deployments.

---

## ⚠️ CRITICAL: Kernel RNG Hardening

### `random.trust_cpu=off` - CPU Hardware RNG Distrust

> **🚨 EXTREME WARNING 🚨**
>
> **THIS SYSTEM WILL BLOCK RATHER THAN PERFORM UNSECURE OPERATIONS**
>
> **Your system will COMPLETELY HALT any operation requiring entropy if insufficient entropy is available. This includes:**
> - SSH connections
> - TLS/SSL operations
> - Key generation
> - System boot process
> - Cryptographic operations in Emercoin
>
> **DO NOT ENABLE THIS WITHOUT ALTERNATIVE ENTROPY SOURCES**

> **✅ FOR PRIVATENESS.NETWORK DEPLOYMENTS:**
>
> This project uses **Gibson's Ultra-High Entropy PRNG** (`pyuheprng`) + **Emercoin Core's embedded RC4OK**.
> With this architecture, entropy shortage is **NOT a concern**. The warning above applies to generic deployments only.

### What This Does

The `random.trust_cpu=off` kernel parameter instructs the Linux kernel to **completely distrust** CPU-provided hardware random number generation via RDRAND/RDSEED instructions.

**Why you might want this:**
- Concerns about potential backdoors in Intel/AMD CPU RNG implementations
- NSA/adversary compromise of hardware RNG
- Compliance requirements for non-hardware entropy
- Defense-in-depth cryptographic security posture

**Technical details:**
- Intel RDRAND/RDSEED instructions are used to seed `/dev/random` and `/dev/urandom`
- Some security researchers distrust these instructions due to lack of transparency
- With `random.trust_cpu=off`, kernel will NOT use these instructions
- System must gather entropy from:
  - **Gibson's Ultra-High Entropy PRNG** (`pyuheprng`) - Privateness.network solution
  - **Emercoin Core's embedded RC4OK** - Built-in high-quality entropy
  - Disk I/O timing
  - Network interrupts
  - Hardware RNG devices (`/dev/hwrng`)
  - Software entropy daemons (haveged, rng-tools) - fallback/generic systems

### Implementation

**Step 1: Install Alternative Entropy Source (REQUIRED)**

**For Privateness.network deployments:**

```bash
# Install pyuheprng (Gibson's Ultra-High Entropy PRNG)
# Already in requirements.txt - installed via:
cd /home/pi/enum-server
pip3 install -r requirements.txt

# pyuheprng integrates with system entropy pool
# Combined with Emercoin Core's RC4OK = no entropy shortage

# Verify entropy is being generated
watch -n 1 cat /proc/sys/kernel/random/entropy_avail
# Should maintain >3000 consistently with pyuheprng + RC4OK
```

**For generic/fallback systems:**

```bash
# Option A: haveged (software entropy daemon)
sudo apt install haveged
sudo systemctl enable haveged
sudo systemctl start haveged

# Option B: Hardware RNG (if available)
ls -la /dev/hwrng
sudo apt install rng-tools
sudo systemctl enable rng-tools
sudo systemctl start rng-tools
```

**Step 2: Modify GRUB Configuration**

```bash
# Backup current GRUB config
sudo cp /etc/default/grub /etc/default/grub.backup

# Edit GRUB
sudo nano /etc/default/grub

# Modify this line (example):
# FROM:
GRUB_CMDLINE_LINUX_DEFAULT="quiet splash"

# TO:
GRUB_CMDLINE_LINUX_DEFAULT="quiet splash random.trust_cpu=off"

# Update GRUB bootloader
sudo update-grub

# REBOOT REQUIRED
sudo reboot
```

**Step 3: Verify After Reboot**

```bash
# Check kernel command line
cat /proc/cmdline | grep random.trust_cpu

# Should output: ... random.trust_cpu=off ...

# Check kernel RNG status
dmesg | grep -i random

# Check entropy pool
cat /proc/sys/kernel/random/entropy_avail
# Must be >1000 for normal operation
# With pyuheprng + RC4OK: typically >3000

# Test entropy generation rate
for i in {1..10}; do 
  cat /proc/sys/kernel/random/entropy_avail
  sleep 1
done
# Should NOT drop to zero
# With pyuheprng + RC4OK: will remain consistently high
```

### Expected Behavior

**Normal Operation (WITH pyuheprng + RC4OK - Privateness.network):**
- System boots normally without delays
- Entropy pool consistently maintains >3000
- Zero performance impact
- All cryptographic operations proceed instantly
- Gibson's PRNG provides ultra-high quality entropy
- Emercoin's RC4OK provides additional entropy layer

**Normal Operation (WITH alternative entropy - generic systems):**
- System boots normally
- Entropy pool stays >1000
- No noticeable performance impact
- Cryptographic operations proceed normally

**FAILURE MODE (WITHOUT alternative entropy - DO NOT DEPLOY):**
- ⚠️ System may hang during boot waiting for entropy
- ⚠️ SSH connections may block for minutes
- ⚠️ SSL/TLS handshakes may timeout
- ⚠️ Emercoin wallet operations may freeze
- ⚠️ Random number generation blocks indefinitely

### Monitoring

**Create entropy monitoring script:**

```bash
cat > ~/check_entropy.sh << 'EOF'
#!/bin/bash
THRESHOLD=1000
ENTROPY=$(cat /proc/sys/kernel/random/entropy_avail)

if [ "$ENTROPY" -lt "$THRESHOLD" ]; then
    echo "$(date): CRITICAL - Entropy low: $ENTROPY" | tee -a /var/log/entropy.log
    # Optional: send alert
else
    echo "$(date): OK - Entropy: $ENTROPY"
fi
EOF

chmod +x ~/check_entropy.sh

# Add to crontab for monitoring
(crontab -l 2>/dev/null; echo "*/5 * * * * /home/pi/check_entropy.sh") | crontab -
```

### Rollback Procedure

If system becomes unusable:

```bash
# Boot into GRUB menu (hold Shift during boot)
# Press 'e' to edit boot entry
# Remove 'random.trust_cpu=off' from kernel line
# Press F10 to boot

# Once booted, permanently remove:
sudo nano /etc/default/grub
# Remove random.trust_cpu=off from GRUB_CMDLINE_LINUX_DEFAULT
sudo update-grub
sudo reboot
```

### Additional Hardening

**Combine with other kernel parameters:**

```bash
GRUB_CMDLINE_LINUX_DEFAULT="quiet random.trust_cpu=off \
  random.trust_bootloader=off \
  slab_nomerge \
  init_on_alloc=1 \
  init_on_free=1 \
  page_alloc.shuffle=1 \
  pti=on \
  vsyscall=none \
  debugfs=off"
```

**Explanation:**
- `random.trust_bootloader=off`: Don't trust bootloader-provided entropy
- `slab_nomerge`: Prevent kernel memory allocator optimizations (anti-exploitation)
- `init_on_alloc=1`: Zero memory on allocation (prevent info leaks)
- `init_on_free=1`: Zero memory on free (prevent use-after-free)
- `page_alloc.shuffle=1`: Randomize page allocator freelists
- `pti=on`: Force Page Table Isolation (Meltdown mitigation)
- `vsyscall=none`: Disable legacy vsyscall interface
- `debugfs=off`: Disable debug filesystem

---

## Network Hardening

### Firewall Configuration

```bash
# UFW rules for ENUM backend
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp comment 'SSH'
sudo ufw allow 8080/tcp comment 'ENUM Backend'
sudo ufw allow 80/tcp comment 'HTTP'
sudo ufw allow 443/tcp comment 'HTTPS'
sudo ufw enable

# Rate limiting
sudo ufw limit 22/tcp
sudo ufw limit 8080/tcp
```

### Emercoin RPC Security

```bash
# Edit Emercoin config
nano ~/.emercoin/emercoin.conf

# Add/modify:
rpcallowip=127.0.0.1
rpcbind=127.0.0.1
rpcuser=$(openssl rand -hex 16)
rpcpassword=$(openssl rand -hex 32)
```

---

## File System Hardening

```bash
# Read-only /boot
echo "/boot    /boot    none    ro,bind    0 0" | sudo tee -a /etc/fstab

# Secure /tmp
echo "tmpfs    /tmp    tmpfs    defaults,noexec,nosuid,nodev    0 0" | sudo tee -a /etc/fstab

# Remount
sudo mount -o remount /boot
sudo mount -o remount /tmp
```

---

## Summary

**For Privateness.network deployments (WITH pyuheprng + RC4OK):**

✅ **Ready to deploy `random.trust_cpu=off`**
- Gibson's Ultra-High Entropy PRNG provides superior entropy
- Emercoin Core's RC4OK provides additional entropy layer
- Maintains >3000 entropy pool consistently
- Zero blocking risk
- Zero performance impact
- No additional configuration needed (installed via requirements.txt)

**For generic systems (WITHOUT pyuheprng):**

Before enabling `random.trust_cpu=off`:

1. ✅ Install and verify haveged or hardware RNG
2. ✅ Confirm entropy stays >1000 consistently
3. ✅ Test SSH, TLS, and Emercoin operations
4. ✅ Document rollback procedure
5. ✅ Set up entropy monitoring

**This is a trade-off:**
- ✅ **Gain**: Protection against CPU RNG backdoors
- ⚠️ **Risk**: System blocking if entropy sources fail (mitigated by pyuheprng)
- ⚠️ **Complexity**: Requires alternative entropy management (handled by pyuheprng)

**Recommended for:**
- Privateness.network deployments (pyuheprng + RC4OK = optimal)
- High-security deployments
- Paranoid security posture
- Compliance requirements

**NOT recommended for:**
- Generic systems without alternative entropy sources
- Systems without monitoring infrastructure
