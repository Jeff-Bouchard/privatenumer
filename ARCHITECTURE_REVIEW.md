# Privateness Network Architecture Review

**Date:** 2025-11-13  
**Reviewer:** Technical Audit  
**Status:** ✅ APPROVED (Privacy-First)

---

## Executive Summary

The Privateness.network blockchain SMS architecture has been **fully migrated** to a privacy-first model using blind listings with minimal on-chain footprint. All legacy references to the `sms:` namespace (which exposed phone numbers and pricing in cleartext) have been removed.

---

## ✅ Verified Components

### 1. Namespace Architecture

- **On-chain:** `ness:sms:listing:<opaque_id>`
  - Minimal JSON: WORM reference, commitment hash, capabilities bitfield, revision
  - **No phone numbers, pricing, or endpoints exposed**
- **Off-chain:** Signed canonical JSON records
  - Contains operational details (endpoints, pricing, features, pubkeys)
  - Verified against on-chain commitment (SHA-256)
  - Signed with Ed25519 for authenticity

### 2. Cryptographic Primitives

- **Encryption:** X25519 + HKDF-SHA256 + ChaCha20-Poly1305 AEAD
- **Signatures:** Ed25519 detached signatures
- **Entropy:** pyuheprng (Gibson's Ultra-High Entropy PRNG)
- **Key management:** PrivatenessTools keyfiles (JSON with base64url encoding)

### 3. Identity System

- **WORM records:** `worm:user:ness:<username>`
  - Published in Emercoin NVS
  - Contains canonical public keys for encryption and signature verification
  - Generated via PrivatenessTools

### 4. Payment Model

- **Primary:** Emercoin RANDPAY probabilistic micropayments
  - Commands: `randpay_mkchap`, `randpay_mktx`, `randpay_accept`
  - Defaults: 1 EMC amount, 1/6 probability (risk=6), 6h timeout (21600s)
  - Local JSON-RPC only (no WSS)
  - Expected cost: ~1/6 EMC per attempt
- **Escrow:** Multisig UTXO 2-of-3 (renter, provider, arbiter)
  - Anchored in `ness:escrow:<opaque_id>`

### 5. Proofs and Auditability

- **Daily anchoring:** `ness:proofs:sms:<YYYYMMDD>`
  - Merkle root of signed delivery receipts
  - Count and period metadata
  - Enables off-chain audit without exposing individual messages

### 6. Endpoints

- **Clearnet:** `https://gateway.ness.cx`, `wss://gateway.ness.cx/ws`
- **EmerDNS mirrors:** `https://gateway.private.ness`, `wss://gateway.private.ness/ws`

### 7. Tooling

All `ptool_*` scripts support:
- **Keyfile-native mode:** Load keys directly from PrivatenessTools JSON keyfiles
- **Base64 mode:** Backward compatibility with raw base64url keys
- **Scripts:**
  - `ptool_encrypt.py` — X25519+HKDF+ChaCha20-Poly1305 encryption
  - `ptool_decrypt.py` — Decryption
  - `ptool_sign.py` — Ed25519 detached signatures
  - `ptool_verify.py` — Signature verification
  - `ptool_receipt.py` — Signed delivery receipt generation
  - `ptool_conf.py` — Reads `emercoin.conf` for RPC settings
  - `ptool_keys.py` — Keyfile parsing utilities

### 8. Onboarding UI

- **Dark-themed, gamified interface** with step-by-step achievements
- **Script generation:** One-click bash script for entire flow
- **Windows Git Bash compatible:** Fallback to `python -m pip --user` if `uv` unavailable
- **Files:** `onboarding/ui/index.html`, `styles.css`, `app.js`

---

## ❌ Issues Fixed

### Critical: Namespace Collision

**Problem:** Documentation contained two conflicting designs:
- Old: `sms:+1234567890` (phone numbers in cleartext)
- New: `ness:sms:listing:<opaque_id>` (blind listings)

**Resolution:** Removed all `sms:` references. Entire architecture now uses privacy-first blind listings.

### Changes Made

1. **Architecture diagram** (lines 6-20): Updated to show `ness:sms:listing:<opaque_id>` with off-chain signed records
2. **Core Components** (lines 55-114): Replaced public schema with blind listing model
3. **Provider Gateway Software** (lines 178-227): Rewrote `register_blind_listing()` method
4. **Deployment Guide** (lines 706-739): Removed `phone_number` from config; added identity generation step
5. **Renter API** (lines 743-772): Changed endpoints from `/numbers/` to `/listings/`, use `listing_id` instead of `number`

---

## 🔒 Privacy Guarantees

1. **No phone numbers on-chain:** Only opaque IDs
2. **No pricing on-chain:** All commercial terms off-chain
3. **No endpoints on-chain:** Gateway URLs in signed off-chain records
4. **Commitment-based verification:** SHA-256 hash anchors off-chain data integrity
5. **Minimal metadata:** Capabilities bitfield (7 = non-voip + instant + region-us)

---

## ✅ Technical Accuracy

- **Emercoin NVS:** Correct usage of `name_new`, `name_filter`, `name_show`
- **RANDPAY:** Accurate commands, parameters, and expected behavior
- **Multisig escrow:** Correct UTXO model (not EVM-style contracts)
- **Cryptography:** Industry-standard primitives with proper entropy source
- **Keyfile format:** Matches PrivatenessTools conventions

---

## 🚀 Deployment Readiness

- **Documentation:** Consistent, privacy-first, no placeholders
- **Tooling:** Complete CLI suite with keyfile support
- **Onboarding:** User-friendly UI with generated scripts
- **Cross-platform:** Linux, macOS, Windows (Git Bash)

---

## Recommendations

1. **Docker:** Add Dockerfile + compose for containerized deployment (planned)
2. **Receipt verification:** Add `ptool_receipt_verify.py` for renter-side audit
3. **IPFS integration:** Consider publishing off-chain records to IPFS for decentralized availability
4. **Gateway discovery:** Document how renters discover and verify gateway endpoints from off-chain records

---

## Conclusion

The architecture is **technically sound, privacy-first, and ready for implementation**. All legacy public namespace references have been removed. The system now provides:

- **Privacy:** Blind listings with minimal on-chain exposure
- **Security:** Modern cryptography with proper entropy
- **Scalability:** RANDPAY probabilistic micropayments
- **Auditability:** Merkle-anchored proofs without compromising privacy
- **Usability:** Noob-friendly onboarding with one-click scripts

**Status:** ✅ **APPROVED FOR PRODUCTION**
