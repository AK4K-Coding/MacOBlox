"""Discord Rich Presence for MacOBlox over Discord IPC Unix sockets."""

from __future__ import annotations

import json
import logging
import os
import socket
import struct
import time
import uuid

log = logging.getLogger("macoblox.discord")

CLIENT_ID = "1468188794309050523"


class DiscordRPC:
    """Manages connection to local Discord client and Rich Presence updates."""

    def __init__(self, client_id: str = CLIENT_ID):
        self.client_id = client_id
        self.sock: socket.socket | None = None
        self._connected = False

    def _find_socket(self) -> list[str]:
        candidates = []
        uid = os.getuid()
        runtime = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{uid}")
        for base in (runtime, os.environ.get("TMPDIR", "/tmp"), "/tmp"):
            if not base or not os.path.isdir(base):
                continue
            for i in range(10):
                path = os.path.join(base, f"discord-ipc-{i}")
                if os.path.exists(path):
                    candidates.append(path)
        return candidates

    def connect(self) -> bool:
        if self._connected and self.sock:
            return True
        for path in self._find_socket():
            try:
                s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                s.settimeout(2.0)
                s.connect(path)
                # Opcode 0: Handshake
                payload = json.dumps({"v": 1, "client_id": self.client_id}).encode("utf-8")
                s.sendall(struct.pack("<II", 0, len(payload)) + payload)
                hdr = s.recv(8)
                if len(hdr) == 8:
                    _op, length = struct.unpack("<II", hdr)
                    body = s.recv(length)
                    data = json.loads(body.decode("utf-8"))
                    if data.get("cmd") == "DISPATCH" and data.get("evt") == "READY":
                        self.sock = s
                        self._connected = True
                        log.info("Connected to Discord IPC on %s", path)
                        return True
                s.close()
            except Exception as e:
                log.debug("Failed connecting to %s: %s", path, e)
        return False

    def update_presence(
        self,
        details: str = "Playing Roblox",
        state: str = "In Game",
        start_time: float | None = None,
        large_image: str = "macoblox",
        large_text: str = "Mac O’ Blox",
    ) -> bool:
        if not self._connected:
            if not self.connect():
                return False
        activity: dict = {
            "details": details,
            "state": state,
            "assets": {
                "large_image": large_image,
                "large_text": large_text,
            },
        }
        if start_time:
            activity["timestamps"] = {"start": int(start_time)}
        message = {
            "cmd": "SET_ACTIVITY",
            "args": {
                "pid": os.getpid(),
                "activity": activity,
            },
            "nonce": str(uuid.uuid4()),
        }
        try:
            payload = json.dumps(message).encode("utf-8")
            assert self.sock is not None
            self.sock.sendall(struct.pack("<II", 1, len(payload)) + payload)
            hdr = self.sock.recv(8)
            if len(hdr) == 8:
                _op, length = struct.unpack("<II", hdr)
                self.sock.recv(length)
            return True
        except Exception as e:
            log.debug("Failed to send presence: %s", e)
            self.close()
            return False

    def clear_presence(self):
        if not self._connected or not self.sock:
            return
        try:
            message = {
                "cmd": "SET_ACTIVITY",
                "args": {
                    "pid": os.getpid(),
                    "activity": None,
                },
                "nonce": str(uuid.uuid4()),
            }
            payload = json.dumps(message).encode("utf-8")
            self.sock.sendall(struct.pack("<II", 1, len(payload)) + payload)
            hdr = self.sock.recv(8)
            if len(hdr) == 8:
                _op, length = struct.unpack("<II", hdr)
                self.sock.recv(length)
        except Exception:
            pass

    def close(self):
        self.clear_presence()
        self._connected = False
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None
