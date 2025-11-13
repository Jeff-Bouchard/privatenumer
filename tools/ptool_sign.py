import argparse
import base64
from cryptography.hazmat.primitives.asymmetric import ed25519


def b64url_decode(s: str) -> bytes:
    s = s.strip()
    pad = '=' * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def b64url_encode(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b'=').decode()


def main():
    p = argparse.ArgumentParser(description='ptool-sign: Ed25519 detached signature (base64url)')
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--priv-b64', help='Ed25519 private key (base64url, 32 or 64 bytes)')
    g.add_argument('--priv-keyfile', help='Path to JSON keyfile with base64url Ed25519 private key')
    p.add_argument('--priv-field', default='ed25519.private', help='Dot path to base64url field in keyfile (default: ed25519.private)')
    p.add_argument('--in', dest='infile', required=True, help='Message input file')
    p.add_argument('--out', dest='outfile', required=True, help='Signature output file (base64url)')
    args = p.parse_args()

    if args.priv_keyfile:
        from ptool_keys import load_b64url_from_keyfile
        sk_bytes = load_b64url_from_keyfile(args.priv_keyfile, args.priv_field)
    else:
        sk_bytes = b64url_decode(args.priv_b64)
    if len(sk_bytes) == 32:
        private_key = ed25519.Ed25519PrivateKey.from_private_bytes(sk_bytes)
    elif len(sk_bytes) == 64:
        private_key = ed25519.Ed25519PrivateKey.from_private_bytes(sk_bytes[:32])
    else:
        raise SystemExit('invalid Ed25519 private key length')

    with open(args.infile, 'rb') as f:
        msg = f.read()

    sig = private_key.sign(msg)

    with open(args.outfile, 'w', encoding='utf-8') as f:
        f.write(b64url_encode(sig))


if __name__ == '__main__':
    main()
