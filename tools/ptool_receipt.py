import argparse
import base64
import json
from hashlib import sha256
from datetime import datetime, timezone
from cryptography.hazmat.primitives.asymmetric import ed25519


def b64url_decode(s: str) -> bytes:
    s = s.strip()
    pad = '=' * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def b64url_encode(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b'=').decode()


def main():
    p = argparse.ArgumentParser(description='ptool-receipt: build and sign delivery receipt (Ed25519)')
    p.add_argument('--from-priv-b64', required=True, help='Issuer Ed25519 private key (base64url, 32 or 64 bytes)')
    p.add_argument('--from-pub-b64', required=True, help='Issuer Ed25519 public verify key (base64url, 32 bytes)')
    p.add_argument('--to-pub-b64', required=False, help='Counterparty Ed25519 public verify key (base64url)')
    p.add_argument('--to-id', required=False, help='Opaque listing id (if not providing to-pub-b64)')
    p.add_argument('--envelope', required=True, help='Path to envelope file (base64url)')
    p.add_argument('--out', required=True, help='Output JSON file')
    args = p.parse_args()

    if not (args.to_pub_b64 or args.to_id):
        raise SystemExit('must provide --to-pub-b64 or --to-id')

    with open(args.envelope, 'r', encoding='utf-8') as f:
        env_b64 = f.read().strip()
    env_bytes = b64url_decode(env_b64)
    msg_hash = sha256(env_bytes).digest()

    sk_bytes = b64url_decode(args.from_priv_b64)
    if len(sk_bytes) == 32:
        sk = ed25519.Ed25519PrivateKey.from_private_bytes(sk_bytes)
    elif len(sk_bytes) == 64:
        sk = ed25519.Ed25519PrivateKey.from_private_bytes(sk_bytes[:32])
    else:
        raise SystemExit('invalid Ed25519 private key length')

    ts = datetime.now(timezone.utc).isoformat()

    receipt = {
        'msg_hash': b64url_encode(msg_hash),
        'ts': ts,
        'from': args.from_pub_b64,
    }
    if args.to_pub_b64:
        receipt['to'] = args.to_pub_b64
    else:
        receipt['to'] = {'listing': args.to_id}

    # Canonical bytes (sorted keys, no whitespace)
    canon = json.dumps(receipt, separators=(',', ':'), sort_keys=True).encode('utf-8')
    sig = sk.sign(canon)
    receipt['sig'] = b64url_encode(sig)

    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(receipt, f, separators=(',', ':'), sort_keys=True)


if __name__ == '__main__':
    main()
