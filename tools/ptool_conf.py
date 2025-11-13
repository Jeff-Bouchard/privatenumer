import argparse
import json
import os
from pathlib import Path

DEFAULT_LINUX = Path.home() / ".emercoin" / "emercoin.conf"
DEFAULT_WINDOWS = Path(os.environ.get("APPDATA", os.path.expanduser("~"))) / "Emercoin" / "emercoin.conf"


def parse_conf(path: Path) -> dict:
    cfg = {}
    if not path.exists():
        return cfg
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                k, v = line.split('=', 1)
                cfg[k.strip()] = v.strip()
    # Normalize common fields
    out = {
        'rpcuser': cfg.get('rpcuser'),
        'rpcpassword': cfg.get('rpcpassword'),
        'rpcconnect': cfg.get('rpcconnect', '127.0.0.1'),
        'rpcport': int(cfg['rpcport']) if 'rpcport' in cfg else 6662,
        'datadir': cfg.get('datadir'),
    }
    return out


def main():
    p = argparse.ArgumentParser(description='ptool-conf: read emercoin.conf and output RPC settings as JSON')
    p.add_argument('--path', help='Path to emercoin.conf. Defaults to standard OS location.')
    args = p.parse_args()

    if args.path:
        path = Path(args.path)
    else:
        path = DEFAULT_WINDOWS if os.name == 'nt' else DEFAULT_LINUX

    conf = parse_conf(path)
    conf['path'] = str(path)
    print(json.dumps(conf, separators=(',', ':'), sort_keys=True))


if __name__ == '__main__':
    main()
