# Raft Lite — Consensus Algorithm (LAB 3)

This repository contains an implementation of a simplified **Raft consensus protocol (Raft Lite)** developed as part of **LAB 3 — Consensus Deployment** for the Distributed Computing course.  
The system is deployed and tested on **AWS EC2 instances** and demonstrates leader election, log replication, and fault tolerance.

---

## Overview

Raft Lite is a simplified version of the Raft consensus algorithm.  
It focuses on the core ideas of consensus without advanced features such as log compaction or persistent storage.

The implementation demonstrates:
- Leader-based coordination
- Majority-based agreement
- Crash-stop failure handling
- Eventual consistency across distributed nodes

---

## Features

- **Leader Election**
  - Nodes start as Followers
  - Leader is elected using majority voting
  - Randomized election timeouts prevent split votes

- **Heartbeats**
  - Leader periodically sends heartbeats
  - Followers reset election timers on heartbeat receipt

- **Log Replication**
  - Clients send commands to the leader
  - Leader replicates commands to followers
  - Entries are committed after majority acknowledgment

- **Fault Tolerance**
  - Leader crash triggers a new election
  - Followers recover and catch up after restart

---

## System Architecture

- **Nodes:** 3 EC2 instances (A, B, C)
- **Roles:** Follower, Candidate, Leader
- **Communication:** HTTP (Flask + Requests)
- **Failure Model:** Crash-stop
- **Timing Model:** Asynchronous with timeouts

Each node maintains the following state:
- `currentTerm`
- `votedFor`
- `log[]`
- `commitIndex`
- `state ∈ {Follower, Candidate, Leader}`

---

## Requirements

- Python 3.8+
- Flask
- Requests

Install dependencies:
```bash
pip install flask requests
