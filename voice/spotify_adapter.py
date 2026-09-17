#!/usr/bin/env python3
import argparse
import http.server
import json
import os
import pathlib
import sys
import time
import urllib.parse
import urllib.request
import webbrowser

TOKEN_FILE = pathlib.Path(os.environ.get("SPOTIFY_TOKEN_FILE", "/home/node/.openclaw/spotify.json"))
API = "https://api.spotify.com/v1"
AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
SCOPES = "user-read-playback-state user-modify-playback-state user-read-currently-playing"

def load_token():
    if TOKEN_FILE.exists():
        return json.loads(TOKEN_FILE.read_text())
    return None

def save_token(data):
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    data["obtained_at"] = int(time.time())
    TOKEN_FILE.write_text(json.dumps(data, indent=2))
    TOKEN_FILE.chmod(0o600)

def ensure_token():
    tok = load_token()
    if not tok:
        print(f"not authenticated. run: python3 {sys.argv[0]} auth", file=sys.stderr)
        sys.exit(3)
    if tok.get("expires_in") and tok.get("obtained_at") and (
        time.time() > tok["obtained_at"] + tok["expires_in"] - 60
    ):
        data = urllib.parse.urlencode({
            "grant_type": "refresh_token",
            "refresh_token": tok["refresh_token"],
            "client_id": os.environ["SPOTIFY_CLIENT_ID"],
            "client_secret": os.environ["SPOTIFY_CLIENT_SECRET"],
        }).encode()
        req = urllib.request.Request(TOKEN_URL, data=data)
        with urllib.request.urlopen(req) as r:
            j = json.loads(r.read().decode())
        tok.update(j)
        save_token(tok)
    return tok["access_token"]

def api(method, path, token, body=None, params=None):
    url = f"{API}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    data = json.dumps(body).encode() if body else None
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
    try:
        with urllib.request.urlopen(req) as r:
            txt = r.read().decode()
            return json.loads(txt) if txt else {}
    except urllib.error.HTTPError as e:
        print(e.read().decode(), file=sys.stderr)
        sys.exit(1)

def cmd_auth(args):
    cid = os.environ.get("SPOTIFY_CLIENT_ID", "")
    redir = os.environ.get("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")
    if not cid:
        print("set SPOTIFY_CLIENT_ID/SECRET/REDIRECT_URI", file=sys.stderr)
        sys.exit(2)
    state = os.urandom(8).hex()
    params = {"client_id": cid, "response_type": "code", "redirect_uri": redir, "scope": SCOPES, "state": state}
    url = AUTH_URL + "?" + urllib.parse.urlencode(params)
    print(f"Open: {url}")
    try:
        webbrowser.open(url)
    except OSError:
        pass
    code_holder = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            qs = urllib.parse.parse_qs(parsed.query)
            code = qs.get("code", [None])[0]
            print(f"hit: path={parsed.path} has_code={bool(code)} from={self.client_address[0]}", flush=True)
            if code:
                code_holder["code"] = code
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Authorized. You can close this window.")
        def log_message(self, *a, **k):
            pass

    parsed = urllib.parse.urlparse(redir)
    port = parsed.port or 8888
    deadline = time.time() + 600
    with http.server.HTTPServer(("127.0.0.1", port), Handler) as httpd:
        print(f"Waiting for callback on {redir} ...")
        while not code_holder.get("code") and time.time() < deadline:
            httpd.timeout = max(1, min(30, int(deadline - time.time())))
            httpd.handle_request()
    code = code_holder.get("code")
    if not code:
        print("no code received (timed out after 10 min)", file=sys.stderr)
        sys.exit(1)
    data = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redir,
        "client_id": os.environ["SPOTIFY_CLIENT_ID"],
        "client_secret": os.environ["SPOTIFY_CLIENT_SECRET"],
    }).encode()
    req = urllib.request.Request(TOKEN_URL, data=data)
    with urllib.request.urlopen(req) as r:
        j = json.loads(r.read().decode())
    save_token(j)
    print(f"authenticated, saved to {TOKEN_FILE}")

def cmd_search(args):
    tok = ensure_token()
    j = api("GET", "/search", tok, params={"q": args.query, "type": "track", "limit": "5"})
    for t in j.get("tracks", {}).get("items", []):
        print(f"{t['name']} — {', '.join(a['name'] for a in t['artists'])} [{t['uri']}]")

def cmd_play(args):
    tok = ensure_token()
    params = {}
    if args.device:
        devs = api("GET", "/me/player/devices", tok)
        match = next((d for d in devs.get("devices", []) if args.device.lower() in d["name"].lower()), None)
        if match:
            params["device_id"] = match["id"]
    if args.uri:
        body = {"uris": [args.uri]}
    elif args.query:
        j = api("GET", "/search", tok, params={"q": args.query, "type": "track", "limit": "1"})
        items = j.get("tracks", {}).get("items", [])
        if not items:
            print("no results", file=sys.stderr)
            sys.exit(1)
        body = {"uris": [items[0]["uri"]]}
        print(f"playing: {items[0]['name']} — {items[0]['artists'][0]['name']}")
    else:
        body = None
    api("PUT", "/me/player/play", tok, body=body, params=params or None)
    print("ok")

def cmd_simple(endpoint, args):
    tok = ensure_token()
    mapping = {
        "pause": ("PUT", "/me/player/pause", None),
        "next": ("POST", "/me/player/next", None),
        "prev": ("POST", "/me/player/previous", None),
        "volume": ("PUT", "/me/player/volume", None),
        "status": ("GET", "/me/player", None),
        "queue": ("POST", "/me/player/queue", None),
    }
    method, path, body = mapping[endpoint]
    params = {}
    if endpoint == "volume":
        params["volume_percent"] = args.value
    if endpoint == "queue":
        params["uri"] = args.uri
    j = api(method, path, tok, body=body, params=params or None)
    if j:
        print(json.dumps(j, indent=2))
    else:
        print("ok")

def main():
    p = argparse.ArgumentParser(description="spotify adapter")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("auth")
    s = sub.add_parser("search"); s.add_argument("--query", required=True)
    pl = sub.add_parser("play"); pl.add_argument("--query"); pl.add_argument("--uri"); pl.add_argument("--device")
    for c in ["pause", "next", "prev", "status"]:
        sub.add_parser(c)
    v = sub.add_parser("volume"); v.add_argument("--value", required=True)
    q = sub.add_parser("queue"); q.add_argument("--uri", required=True)
    args = p.parse_args()
    if args.cmd == "auth":
        cmd_auth(args)
    elif args.cmd == "search":
        cmd_search(args)
    elif args.cmd == "play":
        cmd_play(args)
    else:
        cmd_simple(args.cmd, args)

if __name__ == "__main__":
    main()
