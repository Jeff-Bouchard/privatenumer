import argparse
import base64
import json
from hashlib import sha256
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.asymmetric import x25519

try:
    from pyuheprng import UHEPRNG
except Exception as e:
    UHEPRNG = None


def b64url_decode(s: str) -> bytes:
    s = s.strip()
    pad = '=' * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def b64url_encode(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b'=').decode()


def clamp_scalar32(seed: bytes) -> bytes:
    assert len(seed) == 32
    b = bytearray(seed)
    b[0] &= 248
    b[31] &= 127
    b[31] |= 64
    return bytes(b)


def derive_key(shared_secret: bytes) -> bytes:
    hkdf = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b'privateness-sms-v1')
    return hkdf.derive(shared_secret)


def main():
    p = argparse.ArgumentParser(description='ptool-encrypt: X25519+HKDF+ChaCha20-Poly1305 with pyuheprng entropy')
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--peer-pub-b64', help='Recipient X25519 public key (base64url)')
    g.add_argument('--peer-pub-keyfile', help='Path to JSON keyfile with recipient X25519 public key')
    p.add_argument('--peer-pub-field', default='x25519.public', help='Dot path to base64url field in keyfile (default: x25519.public)')
    p.add_argument('--in', dest='infile', required=True, help='Plaintext input file')
    p.add_argument('--out', dest='outfile', required=True, help='Envelope output file (base64url)')
    args = p.parse_args()

    if UHEPRNG is None:
        raise SystemExit('pyuheprng not available; pip install pyuheprng')

    rng = UHEPRNG()
    with open(args.infile, 'rb') as f:
        plaintext = f.read()

    if args.peer_pub_keyfile:
        # lazy import helper to avoid hard dep when not used
        from ptool_keys import load_b64url_from_keyfile
        peer_pub_bytes = load_b64url_from_keyfile(args.peer_pub_keyfile, args.peer_pub_field)
    else:
        peer_pub_bytes = b64url_decode(args.peer_pub_b64)

    peer_pub = x25519.X25519PublicKey.from_public_bytes(peer_pub_bytes)

    # Ephemeral private from pyuheprng, clamped
    raw_priv = rng.random_bytes(32)
    ephem_priv = x25519.X25519PrivateKey.from_private_bytes(clamp_scalar32(raw_priv))
    ephem_pub = ephem_priv.public_key().public_bytes_raw()

    shared = ephem_priv.exchange(peer_pub)
    key = derive_key(shared)

    nonce = rng.random_bytes(12)
    aead = ChaCha20Poly1305(key)
    ciphertext = aead.encrypt(nonce, plaintext, None)

    envelope = ephem_pub + nonce + ciphertext
    with open(args.outfile, 'w', encoding='utf-8') as f:
        f.write(b64url_encode(envelope))


if __name__ == '__main__':
    main()
