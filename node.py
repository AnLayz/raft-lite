import time
import threading
import random
import requests
from flask import Flask, request, jsonify
from argparse import ArgumentParser

app = Flask(__name__)
node = None


class RaftNode:
    def __init__(self, node_id, port, peers):
        self.id = node_id
        self.port = port
        self.peers = peers

        self.state = "Follower"
        self.currentTerm = 0
        self.votedFor = None

        self.log = []          # [{term, command}]
        self.commitIndex = -1

        self.lastHeartbeat = time.time()
        self.electionTimeout = random.uniform(2, 4)

        self.votesReceived = 0
        self.lock = threading.Lock()

    # ---------------- Election ----------------

    def start_election(self):
        with self.lock:
            self.state = "Candidate"
            self.currentTerm += 1
            self.votedFor = self.id
            self.votesReceived = 1
            print(f"[Node {self.id}] Timeout → Candidate (term {self.currentTerm})")

        for peer in self.peers:
            threading.Thread(
                target=self.request_vote,
                args=(peer, self.currentTerm),
                daemon=True
            ).start()

    def request_vote(self, peer, term):
        try:
            r = requests.post(
                f"http://{peer}/request_vote",
                json={"term": term, "candidateId": self.id},
                timeout=0.5
            ).json()

            if r.get("voteGranted"):
                with self.lock:
                    self.votesReceived += 1
                    if self.state == "Candidate" and self.votesReceived > len(self.peers) // 2:
                        self.become_leader()
        except:
            pass

    def become_leader(self):
        self.state = "Leader"
        print(f"[Node {self.id}] Received majority → Leader (term {self.currentTerm})")
        threading.Thread(target=self.heartbeat_loop, daemon=True).start()

    # ---------------- Heartbeats ----------------

    def heartbeat_loop(self):
        while self.state == "Leader":
            for peer in self.peers:
                try:
                    requests.post(
                        f"http://{peer}/append_entries",
                        json={
                            "term": self.currentTerm,
                            "leaderId": self.id,
                            "entries": self.log,
                            "commitIndex": self.commitIndex
                        },
                        timeout=0.3
                    )
                except:
                    pass
            time.sleep(0.5)

    # ---------------- Main Loop ----------------

    def tick(self):
        while True:
            time.sleep(0.5)
            if self.state != "Leader" and time.time() - self.lastHeartbeat > self.electionTimeout:
                self.start_election()
                self.lastHeartbeat = time.time()


# ---------------- API ----------------

@app.route("/request_vote", methods=["POST"])
def request_vote():
    data = request.json
    with node.lock:
        if data["term"] > node.currentTerm:
            node.currentTerm = data["term"]
            node.votedFor = data["candidateId"]
            node.state = "Follower"
            return jsonify({"voteGranted": True})
    return jsonify({"voteGranted": False})


@app.route("/append_entries", methods=["POST"])
def append_entries():
    data = request.json
    with node.lock:
        if data["term"] >= node.currentTerm:
            node.currentTerm = data["term"]
            node.state = "Follower"
            node.lastHeartbeat = time.time()

            if len(data["entries"]) > len(node.log):
                node.log = data["entries"]
                print(f"[Node {node.id}] Log updated: {node.log}")

            if data["commitIndex"] > node.commitIndex:
                node.commitIndex = data["commitIndex"]
                print(f"[Node {node.id}] Entry committed at index {node.commitIndex}")

    return jsonify({"success": True})


@app.route("/client_command", methods=["POST"])
def client_command():
    if node.state != "Leader":
        return jsonify({"error": "Not leader"}), 403

    cmd = request.json["command"]

    with node.lock:
        entry = {"term": node.currentTerm, "command": cmd}
        node.log.append(entry)
        index = len(node.log) - 1
        print(f"[Leader {node.id}] Append log entry (term={node.currentTerm}, cmd={cmd})")

    acks = 1
    for peer in node.peers:
        try:
            r = requests.post(
                f"http://{peer}/append_entries",
                json={
                    "term": node.currentTerm,
                    "leaderId": node.id,
                    "entries": node.log,
                    "commitIndex": node.commitIndex
                },
                timeout=0.5
            ).json()
            if r.get("success"):
                acks += 1
        except:
            pass

    if acks > len(node.peers) // 2:
        node.commitIndex = index
        print(f"[Leader {node.id}] Entry committed (index={index})")

    return jsonify({"status": "ok"})


# ---------------- Startup ----------------

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--id", required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--peers", required=True)
    args = parser.parse_args()

    node = RaftNode(args.id, args.port, args.peers.split(","))
    threading.Thread(target=node.tick, daemon=True).start()

    app.run(host="0.0.0.0", port=args.port)
