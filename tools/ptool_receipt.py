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
    gf = p.add_mutually_exclusive_group(required=True)
    gf.add_argument('--from-priv-b64', help='Issuer Ed25519 private key (base64url, 32 or 64 bytes)')
    gf.add_argument('--from-priv-keyfile', help='Path to JSON keyfile with base64url Ed25519 private key')
    p.add_argument('--from-priv-field', default='ed25519.private', help='Dot path in keyfile (default: ed25519.private)')

    gp = p.add_mutually_exclusive_group(required=True)
    gp.add_argument('--from-pub-b64', help='Issuer Ed25519 public verify key (base64url, 32 bytes)')
    gp.add_argument('--from-pub-keyfile', help='Path to JSON keyfile with base64url Ed25519 public key')
    p.add_argument('--from-pub-field', default='ed25519.public', help='Dot path in keyfile (default: ed25519.public)')

    gt = p.add_mutually_exclusive_group(required=True)
    gt.add_argument('--to-pub-b64', help='Counterparty Ed25519 public verify key (base64url)')
    gt.add_argument('--to-id', help='Opaque listing id (if not providing to-pub-b64)')

    p.add_argument('--to-pub-keyfile', help='Optional: load counterparty pubkey from JSON keyfile')
    p.add_argument('--to-pub-field', default='ed25519.public', help='Dot path for counterparty pubkey (default: ed25519.public)')

    p.add_argument('--envelope', required=True, help='Path to envelope file (base64url)')
    p.add_argument('--out', required=True, help='Output JSON file')
    args = p.parse_args()

    # load keys depending on mode
    if args.from_priv_keyfile:
        from ptool_keys import load_b64url_from_keyfile
        sk_bytes = load_b64url_from_keyfile(args.from_priv_keyfile, args.from_priv_field)
    else:
        sk_bytes = b64url_decode(args.from_priv_b64)

    if args.from_pub_keyfile:
        from ptool_keys import load_b64url_from_keyfile
        from_pub_b64 = load_b64url_from_keyfile(args.from_pub_keyfile, args.from_pub_field)
        # convert bytes to b64url string for JSON genesis
        from_pub_b64 = base64.urlsafe_b64encode(from_pub_b64).rstrip(b'=').decode()
    else:
        from_pub_b64 = args.from_pub_b64

    with open(args.envelope, 'r', encoding='utf-8') as f:
        env_b64 = f.read().strip()
    env_bytes = b64url_decode(env_b64)
    msg_hash = sha256(env_bytes).digest()

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
        'from': from_pub_b64,
    }
    if args.to_pub_b64:
        receipt['to'] = args.to_pub_b64
    elif args.to_pub_keyfile:
        from ptool_keys import load_b64url_from_keyfile
        to_pub_bytes = load_b64url_from_keyfile(args.to_pub_keyfile, args.to_pub_field)
        receipt['to'] = base64.urlsafe_b64encode(to_pub_bytes).rstrip(b'=').decode()
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
