#!/usr/bin/env python3
"""Polished Linux interface over checkpoint 5's unchanged Ethernet module.

Tkinter owns presentation only. Every discovery announcement and chat message
still travels through DiscoveryChat's AF_PACKET raw socket inside this process.
There is no HTTP server, browser, TCP socket, UDP socket, or localhost API.
"""

from __future__ import annotations

import argparse
import queue
import socket
import threading
import time
import tkinter as tk
from tkinter import ttk

from discovery_chat import DiscoveryChat, PeerHello, ReceivedChat
from ethernet import format_mac
from peer_directory import HELLO_INTERVAL_SECONDS, PeerStatus


INK = "#172033"
MUTED = "#667085"
PAPER = "#F7F6F2"
PANEL = "#FFFFFF"
ACCENT = "#E05A3F"
ACCENT_DARK = "#B8422D"
SEA = "#2D6A6A"
LINE = "#E4E2DC"
WARNING = "#B42318"


class NoIpChatWindow:
    """Render one participant while DiscoveryChat owns all networking."""

    def __init__(self, root: tk.Tk, name: str, geometry: str) -> None:
        self.root = root
        self.chat = DiscoveryChat(name)
        self.events: queue.Queue[object] = queue.Queue()
        self.stopped = threading.Event()
        self.selected_name: str | None = None
        self.peer_rows: list[PeerStatus] = []
        self.peer_signature: tuple[tuple[str, tuple[bytes, ...]], ...] = ()
        self.seen_names: set[str] = set()

        self._configure_window(name, geometry)
        self._build_interface(name)

        self.network_thread = threading.Thread(target=self._network_loop, daemon=True)
        self.network_thread.start()
        self.root.after(100, self._drain_events)
        self.root.after(250, self._refresh_peers)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def _configure_window(self, name: str, geometry: str) -> None:
        self.root.title(f"No-IP Chat · {name}")
        self.root.geometry(geometry)
        self.root.minsize(300, 620)
        self.root.configure(bg=PAPER)

        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TFrame", background=PAPER)
        style.configure("Panel.TFrame", background=PANEL)
        style.configure("Title.TLabel", background=PAPER, foreground=INK, font=("DejaVu Sans", 19, "bold"))
        style.configure("Body.TLabel", background=PAPER, foreground=MUTED, font=("DejaVu Sans", 9))
        style.configure("Panel.TLabel", background=PANEL, foreground=INK, font=("DejaVu Sans", 10))
        style.configure("Small.Panel.TLabel", background=PANEL, foreground=MUTED, font=("DejaVu Sans", 8))
        style.configure("Accent.TButton", background=ACCENT, foreground="white", font=("DejaVu Sans", 9, "bold"), padding=(12, 8))
        style.map("Accent.TButton", background=[("active", ACCENT_DARK), ("disabled", "#C9C7C1")])

    def _build_interface(self, name: str) -> None:
        shell = ttk.Frame(self.root, padding=(16, 14))
        shell.pack(fill="both", expand=True)

        ttk.Label(shell, text="NO-IP CHAT", style="Body.TLabel").pack(anchor="w")
        ttk.Label(shell, text=name, style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            shell,
            text="Ethernet only  ·  EtherType 0x88B5",
            foreground=SEA,
            background=PAPER,
            font=("DejaVu Sans", 9, "bold"),
        ).pack(anchor="w", pady=(1, 10))

        self.alert = tk.Label(shell, text="", bg=PAPER, fg=WARNING, anchor="w", font=("DejaVu Sans", 8, "bold"))
        self.alert.pack(fill="x")

        people = ttk.Frame(shell, style="Panel.TFrame", padding=10)
        people.pack(fill="x", pady=(6, 10))
        ttk.Label(people, text="DISCOVERED PEOPLE", style="Small.Panel.TLabel").pack(anchor="w")
        self.peer_list = tk.Listbox(
            people,
            height=4,
            borderwidth=0,
            highlightthickness=0,
            activestyle="none",
            bg=PANEL,
            fg=INK,
            selectbackground=SEA,
            selectforeground="white",
            font=("DejaVu Sans", 10),
        )
        self.peer_list.pack(fill="x", pady=(6, 2))
        self.peer_list.bind("<<ListboxSelect>>", self._select_peer)
        self.peer_detail = ttk.Label(people, text="Waiting for HELLO announcements…", style="Small.Panel.TLabel")
        self.peer_detail.pack(anchor="w", pady=(4, 0))

        conversation = ttk.Frame(shell, style="Panel.TFrame", padding=10)
        conversation.pack(fill="both", expand=True)
        ttk.Label(conversation, text="CONVERSATION", style="Small.Panel.TLabel").pack(anchor="w")
        self.transcript = tk.Text(
            conversation,
            wrap="word",
            borderwidth=0,
            highlightthickness=0,
            bg=PANEL,
            fg=INK,
            font=("DejaVu Sans", 10),
            padx=2,
            pady=8,
            state="disabled",
        )
        self.transcript.pack(fill="both", expand=True)
        self.transcript.tag_configure("incoming-name", foreground=SEA, font=("DejaVu Sans", 8, "bold"), spacing1=8)
        self.transcript.tag_configure("outgoing-name", foreground=ACCENT_DARK, font=("DejaVu Sans", 8, "bold"), justify="right", spacing1=8)
        self.transcript.tag_configure("incoming", foreground=INK, lmargin2=8, spacing3=5)
        self.transcript.tag_configure("outgoing", foreground=INK, justify="right", rmargin=8, spacing3=5)
        self.transcript.tag_configure("system", foreground=MUTED, font=("DejaVu Sans", 8, "italic"), justify="center", spacing1=7, spacing3=7)
        self._append_system("Broadcast HELLO discovers people; chat stays unicast.")

        compose = ttk.Frame(shell, padding=(0, 10, 0, 0))
        compose.pack(fill="x")
        self.message = tk.Entry(
            compose,
            relief="flat",
            bg=PANEL,
            fg=INK,
            insertbackground=INK,
            font=("DejaVu Sans", 10),
        )
        self.message.pack(side="left", fill="x", expand=True, ipady=9)
        self.message.bind("<Return>", self._send)
        self.send_button = ttk.Button(compose, text="Send", style="Accent.TButton", command=self._send, state="disabled")
        self.send_button.pack(side="left", padx=(8, 0))

        footer = ttk.Frame(shell, padding=(0, 8, 0, 0))
        footer.pack(fill="x")
        ttk.Label(footer, text=f"My MAC  {format_mac(self.chat.own_mac)}", style="Body.TLabel").pack(side="left")
        ttk.Label(footer, text="Trusted lab · no delivery receipt", style="Body.TLabel").pack(side="right")

    def _network_loop(self) -> None:
        next_hello = 0.0
        while not self.stopped.is_set():
            now = time.monotonic()
            if now >= next_hello:
                try:
                    self.chat.announce()
                except OSError:
                    return
                next_hello = now + HELLO_INTERVAL_SECONDS
            try:
                event = self.chat.receive(timeout=0.15)
            except socket.timeout:
                continue
            except OSError:
                return
            self.events.put(event)

    def _drain_events(self) -> None:
        while True:
            try:
                event = self.events.get_nowait()
            except queue.Empty:
                break
            if isinstance(event, ReceivedChat):
                self._append_message(event.sender, event.text, outgoing=False)
            elif isinstance(event, PeerHello) and event.name not in self.seen_names:
                self.seen_names.add(event.name)
                self._append_system(f"Discovered {event.name} from a broadcast HELLO")
        if not self.stopped.is_set():
            self.root.after(100, self._drain_events)

    def _refresh_peers(self) -> None:
        rows = self.chat.peers()
        signature = tuple((row.name, row.macs) for row in rows)
        if signature != self.peer_signature:
            self.peer_signature = signature
            self.peer_rows = rows
            self.peer_list.delete(0, "end")
            for peer in rows:
                marker = "⚠ " if peer.conflicted else "● "
                suffix = "  name conflict" if peer.conflicted else "  available"
                self.peer_list.insert("end", marker + peer.name + suffix)
            self._restore_selection()

        if self.chat.own_name_conflicted():
            self.alert.configure(text="Another computer is announcing your name. Sending is disabled.")
        else:
            self.alert.configure(text="")
        self._update_send_state()
        if not self.stopped.is_set():
            self.root.after(250, self._refresh_peers)

    def _restore_selection(self) -> None:
        if self.selected_name is None:
            return
        for index, peer in enumerate(self.peer_rows):
            if peer.name == self.selected_name:
                self.peer_list.selection_set(index)
                self._show_peer_detail(peer)
                return
        self.selected_name = None
        self.peer_detail.configure(text="Selected person is no longer available")

    def _select_peer(self, _event: object = None) -> None:
        selected = self.peer_list.curselection()
        if not selected:
            return
        peer = self.peer_rows[selected[0]]
        self.selected_name = peer.name
        self._show_peer_detail(peer)
        self._update_send_state()
        self.message.focus_set()

    def _show_peer_detail(self, peer: PeerStatus) -> None:
        addresses = ", ".join(format_mac(mac) for mac in peer.macs)
        state = "ambiguous — sending refused" if peer.conflicted else "direct unicast recipient"
        self.peer_detail.configure(text=f"{addresses}  ·  {state}")

    def _update_send_state(self) -> None:
        selected = next((peer for peer in self.peer_rows if peer.name == self.selected_name), None)
        enabled = selected is not None and not selected.conflicted and not self.chat.own_name_conflicted()
        self.send_button.configure(state="normal" if enabled else "disabled")

    def _send(self, _event: object = None) -> str:
        text = self.message.get().strip()
        if not text or self.selected_name is None:
            return "break"
        try:
            self.chat.send_to(self.selected_name, text)
        except ValueError as error:
            self._append_system(str(error))
        else:
            self._append_message("You", text, outgoing=True)
            self._append_system("Sent means handed to Ethernet; no delivery receipt is claimed.")
            self.message.delete(0, "end")
        return "break"

    def _append_message(self, sender: str, text: str, outgoing: bool) -> None:
        self.transcript.configure(state="normal")
        name_tag = "outgoing-name" if outgoing else "incoming-name"
        text_tag = "outgoing" if outgoing else "incoming"
        self.transcript.insert("end", sender.upper() + "\n", name_tag)
        self.transcript.insert("end", text + "\n", text_tag)
        self.transcript.configure(state="disabled")
        self.transcript.see("end")

    def _append_system(self, text: str) -> None:
        self.transcript.configure(state="normal")
        self.transcript.insert("end", text + "\n", "system")
        self.transcript.configure(state="disabled")
        self.transcript.see("end")

    def close(self) -> None:
        if self.stopped.is_set():
            return
        self.stopped.set()
        self.chat.close()
        self.network_thread.join(timeout=1)
        self.root.destroy()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--geometry", default="420x700+40+40")
    args = parser.parse_args()
    root = tk.Tk()
    NoIpChatWindow(root, args.name, args.geometry)
    root.mainloop()


if __name__ == "__main__":
    main()
