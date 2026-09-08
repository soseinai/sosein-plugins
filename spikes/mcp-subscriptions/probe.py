#!/usr/bin/env python3
"""Local, no-model Codex resource-notification probe. No persistent config edits."""
import argparse
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import tempfile
import threading
import time
import tomllib

URI = "spike://sosein/plan"


def server(log):
    revision = 1
    def send(value):
        print(json.dumps({"jsonrpc": "2.0", **value}), flush=True)
    for line in sys.stdin:
        request = json.loads(line)
        with open(log, "a") as out:
            out.write(json.dumps(request) + "\n")
        method = request.get("method")
        if "id" not in request:
            continue
        if method == "initialize":
            result = {"protocolVersion": "2025-11-25", "capabilities": {
                "resources": {"subscribe": True, "listChanged": True}, "tools": {}},
                "serverInfo": {"name": "subscription-spike", "version": "1"}}
        elif method == "resources/list":
            result = {"resources": [{"uri": URI, "name": "plan", "mimeType": "text/plain"}]}
        elif method == "resources/templates/list":
            result = {"resourceTemplates": []}
        elif method == "tools/list":
            result = {"tools": []}
        elif method == "resources/read":
            result = {"contents": [{"uri": URI, "mimeType": "text/plain", "text": f"revision {revision}"}]}
        elif method in ("resources/subscribe", "resources/unsubscribe", "ping"):
            result = {}
        else:
            send({"id": request["id"], "error": {"code": -32601, "message": "Unsupported method"}})
            continue
        send({"id": request["id"], "result": result})
        if method == "resources/read" and revision == 1:
            # Deliberately unsolicited diagnostic injection. This is NOT proof of
            # a successful subscription: it isolates the notification handler.
            time.sleep(0.2)
            revision = 2
            send({"method": "notifications/resources/updated", "params": {"uri": URI}})
            with open(log, "a") as out:
                out.write(json.dumps({"sent": "notifications/resources/updated", "uri": URI}) + "\n")


def probe(binary, output):
    output.mkdir(parents=True, exist_ok=True)
    wire = output / "wire.jsonl"
    wire.write_text("")
    config_path = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "config.toml"
    config = tomllib.loads(config_path.read_text()) if config_path.exists() else {}
    args = [binary, "app-server"]
    # Disable existing integrations for this subprocess only. Never print config
    # values or copy credentials to the fixture or evidence files.
    for name in config.get("mcp_servers", {}):
        args += ["-c", f"mcp_servers.{name}.enabled=false"]
    for name in config.get("plugins", {}):
        args += ["-c", f"plugins.{name}.enabled=false"]
    args += ["-c", "features.apps=false", "-c", "features.plugins=false",
             "-c", f"mcp_servers.subscription_spike.command={json.dumps(sys.executable)}",
             "-c", "mcp_servers.subscription_spike.args=" + json.dumps([str(Path(__file__).resolve()), "--server", str(wire.resolve())]),
             "-c", "mcp_servers.subscription_spike.enabled=true"]
    events = queue.Queue()
    with tempfile.TemporaryDirectory(prefix="sosein-subscription-cwd-") as cwd, (output / "stderr.log").open("w") as err:
        process = subprocess.Popen(args, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=err, text=True, env={**os.environ, "RUST_LOG": "codex_rmcp_client=info"})
        transcript = []
        def reader():
            for line in process.stdout:
                try:
                    events.put(json.loads(line))
                except json.JSONDecodeError:
                    pass
            events.put({"probe_process_exited": True})
        threading.Thread(target=reader, daemon=True).start()
        def call(i, method, params):
            print(f"Calling {method}", flush=True)
            process.stdin.write(json.dumps({"id": i, "method": method, "params": params}) + "\n")
            process.stdin.flush()
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                event = events.get(timeout=max(0.1, deadline - time.monotonic()))
                if event.get("probe_process_exited"):
                    raise RuntimeError("Codex exited; inspect stderr.log")
                transcript.append(event)
                if event.get("id") == i:
                    return event
            raise TimeoutError(method)
        try:
            initialized = call(1, "initialize", {"clientInfo": {"name": "sosein_subscription_spike", "version": "1"},
                "capabilities": {"experimentalApi": True}})
            started = call(5, "thread/start", {"ephemeral": True, "cwd": cwd})
            if "error" in started:
                raise RuntimeError(started["error"])
            thread_id = started["result"]["thread"]["id"]
            status = call(2, "mcpServerStatus/list", {"threadId": thread_id})
            first = call(3, "mcpServer/resource/read", {"server": "subscription_spike", "uri": URI, "threadId": thread_id})
            # A bounded observation window; no model is started or billed.
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline:
                try:
                    transcript.append(events.get(timeout=0.2))
                except queue.Empty:
                    pass
            second = call(4, "mcpServer/resource/read", {"server": "subscription_spike", "uri": URI, "threadId": thread_id})
            requests = [json.loads(line) for line in wire.read_text().splitlines()]
            assert "error" not in first and "error" not in second, "Resource read failed"
            assert first["result"]["contents"][0]["text"] == "revision 1"
            assert second["result"]["contents"][0]["text"] == "revision 2"
            summary = {"binary_version": subprocess.check_output([binary, "--version"], text=True).strip(),
                       "methods": [r["method"] for r in requests if "method" in r],
                       "first_read": first, "explicit_second_read": second,
                       "app_server_notifications": [e.get("method") for e in transcript if "method" in e],
                       "initialize_error": initialized.get("error"), "status_error": status.get("error")}
            (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
            print(json.dumps(summary, indent=2))
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server")
    parser.add_argument("--codex", default="codex")
    parser.add_argument("--output", type=Path)
    options = parser.parse_args()
    if options.server:
        server(options.server)
    elif options.output:
        probe(options.codex, options.output.resolve())
    else:
        parser.error("Specify --output for probe results")
