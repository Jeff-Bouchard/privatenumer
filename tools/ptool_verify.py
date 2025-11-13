import argparse
import base64
from cryptography.hazmat.primitives.asymmetric import ed25519


def b64url_decode(s: str) -> bytes:
    s = s.strip()
    pad = '=' * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def main():
    p = argparse.ArgumentParser(description='ptool-verify: Ed25519 detached signature verify (base64url)')
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--pub-b64', help='Ed25519 verify public key (base64url, 32 bytes)')
    g.add_argument('--pub-keyfile', help='Path to JSON keyfile with base64url Ed25519 public key')
    p.add_argument('--pub-field', default='ed25519.public', help='Dot path to base64url field in keyfile (default: ed25519.public)')
    p.add_argument('--in', dest='infile', required=True, help='Message input file')
    p.add_argument('--sig', dest='sigfile', required=True, help='Signature input file (base64url)')
    args = p.parse_args()

    if args.pub_keyfile:
        from ptool_keys import load_b64url_from_keyfile
        vk_bytes = load_b64url_from_keyfile(args.pub_keyfile, args.pub_field)
    else:
        vk_bytes = b64url_decode(args.pub_b64)
    if len(vk_bytes) != 32:
        raise SystemExit('invalid Ed25519 public key length')

    with open(args.infile, 'rb') as f:
        msg = f.read()
    with open(args.sigfile, 'r', encoding='utf-8') as f:
        sig_b64 = f.read()
    sig = b64url_decode(sig_b64)

    try:
        ed25519.Ed25519PublicKey.from_public_bytes(vk_bytes).verify(sig, msg)
        # valid
        raise SystemExit(0)
    except Exception:
        # invalid
        raise SystemExit(1)


if __name__ == '__main__':
    main()
