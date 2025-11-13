import argparse
import base64
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.asymmetric import x25519


def b64url_decode(s: str) -> bytes:
    s = s.strip()
    pad = '=' * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def b64url_encode(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b'=').decode()


def derive_key(shared_secret: bytes) -> bytes:
    hkdf = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b'privateness-sms-v1')
    return hkdf.derive(shared_secret)


def main():
    p = argparse.ArgumentParser(description='ptool-decrypt: X25519+HKDF+ChaCha20-Poly1305')
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--priv-b64', help='Recipient X25519 private key (base64url, 32 bytes)')
    g.add_argument('--priv-keyfile', help='Path to JSON keyfile containing base64url X25519 private key')
    p.add_argument('--priv-field', default='x25519.private', help='Dot path to base64url field in keyfile (default: x25519.private)')
    p.add_argument('--in', dest='infile', required=True, help='Envelope input file (base64url)')
    p.add_argument('--out', dest='outfile', required=True, help='Plaintext output file')
    args = p.parse_args()

    if args.priv_keyfile:
        from ptool_keys import load_b64url_from_keyfile
        priv_bytes = load_b64url_from_keyfile(args.priv_keyfile, args.priv_field)
    else:
        priv_bytes = b64url_decode(args.priv_b64)

    priv = x25519.X25519PrivateKey.from_private_bytes(priv_bytes)

    with open(args.infile, 'r', encoding='utf-8') as f:
        envelope_b64 = f.read()
    envelope = b64url_decode(envelope_b64)

    if len(envelope) < 32 + 12 + 16:
        raise SystemExit('invalid envelope length')

    epk = envelope[:32]
    nonce = envelope[32:44]
    ciphertext = envelope[44:]

    peer_pub = x25519.X25519PublicKey.from_public_bytes(epk)
    shared = priv.exchange(peer_pub)
    key = derive_key(shared)

    aead = ChaCha20Poly1305(key)
    plaintext = aead.decrypt(nonce, ciphertext, None)

    with open(args.outfile, 'wb') as f:
        f.write(plaintext)


if __name__ == '__main__':
    main()
