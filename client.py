#!/usr/bin/env python3
import subprocess, json, time, os, select

SERVER = os.path.join(os.path.dirname(__file__), "server.py")
VENV = os.path.join(os.path.dirname(__file__), ".venv", "bin", "python")


class RouteMCPClient:
    def __init__(self):
        self.proc = None
        self._rid = 0

    def start(self):
        self.proc = subprocess.Popen(
            [VENV, SERVER], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        self._send("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "routemcp-client", "version": "1.0"}})
        self._recv()
        self._notif("notifications/initialized")

    def _send(self, method, params=None):
        self._rid += 1
        m = json.dumps({"jsonrpc": "2.0", "id": self._rid, "method": method, "params": params or {}}) + "\n"
        self.proc.stdin.write(m.encode()); self.proc.stdin.flush()

    def _notif(self, method, params=None):
        m = json.dumps({"jsonrpc": "2.0", "method": method, "params": params or {}}) + "\n"
        self.proc.stdin.write(m.encode()); self.proc.stdin.flush()

    def _recv(self, t=5):
        buf = b""; deadline = time.time() + t
        while time.time() < deadline:
            r, _, _ = select.select([self.proc.stdout], [], [], 0.3)
            if r:
                c = self.proc.stdout.read1(4096); buf += c
                if b"\n" in buf: return json.loads(buf.split(b"\n")[0])
        try: return json.loads(buf.strip().split(b"\n")[0])
        except: return {}

    def call(self, tool, args=None):
        self._send("tools/call", {"name": tool, "arguments": args or {}})
        r = self._recv()
        return "\n".join(c.get("text", "") for c in r.get("result", {}).get("content", []))

    def stop(self):
        if self.proc: self.proc.terminate(); self.proc.wait(2)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("command", nargs="?", default="demo", choices=["demo", "route", "ask", "compare", "models", "classify"])
    parser.add_argument("prompt", nargs="*", default=[])
    args = parser.parse_args()

    client = RouteMCPClient()
    client.start()

    try:
        if args.command == "models":
            print(client.call("models"))
        elif args.command == "classify":
            p = " ".join(args.prompt) or "write a python function"
            print(client.call("classify_task", {"prompt": p}))
        elif args.command == "route":
            p = " ".join(args.prompt) or "hello"
            print(client.call("route", {"prompt": p}))
        elif args.command == "ask":
            if len(args.prompt) < 2:
                print("Usage: client.py ask <model> <prompt>")
            else:
                print(client.call("ask", {"model": args.prompt[0], "prompt": " ".join(args.prompt[1:])}))
        elif args.command == "compare":
            p = " ".join(args.prompt) or "hello"
            print(client.call("compare", {"prompt": p, "models": "gemini-2.0-flash,llama-3.3-70b"}))
        elif args.command == "demo":
            print("=== RouteMCP Demo ===\n")
            print("📋 Available models:")
            print(client.call("models")[:500])
            print()
            print("🔍 Classify task:")
            print(client.call("classify_task", {"prompt": "write a python function to sort a list"}))
    finally:
        client.stop()


if __name__ == "__main__":
    main()
