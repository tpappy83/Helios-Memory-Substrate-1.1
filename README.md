
[![Build Status](https://github.com/tpappy83/Helios-Memory-Substrate-1.1/actions/workflows/main.yml/badge.svg)](https://github.com/tpappy83/Helios-Memory-Substrate-1.1/actions/workflows/main.yml) [![License](https://img.shields.io/github/license/tpappy83/Helios-Memory-Substrate-1.1.svg)](LICENSE) [![Issues](https://img.shields.io/github/issues/tpappy83/Helios-Memory-Substrate-1.1.svg)](https://github.com/tpappy83/Helios-Memory-Substrate-1.1/issues) [![Stars](https://img.shields.io/github/stars/tpappy83/Helios-Memory-Substrate-1.1.svg)](https://github.com/tpappy83/Helios-Memory-Substrate-1.1/stargazers)

# Helios Memory Substrate

Helios Memory Substrate is a distributed, high-performance memory architecture designed to support long-context AI systems, agentic workflows, and large-scale vector-based retrieval. It provides a tiered substrate for ingesting, indexing, scoring, and retrieving high-cardinality memory objects with predictable latency and horizontal scalability.

## Vision

Helios is built to solve one problem:
LLMs need memory systems that behave like cognition, not storage.

The substrate is designed for:
- Autonomous agents
- Long-running workflows
- Multi-agent orchestration
- High-volume ingestion pipelines
- Real-time vector retrieval
- Distributed memory clusters

## Core Architecture

### 1. Quark Ingestion Layer
- UUID assignment
- Timestamping
- Batch ingestion
- Pre-processing for vectorization

### 2. Helios Distributed Core
- Cluster-aware memory distribution
- Importance scoring
- Drift-aware decay
- Tiered memory retention
- p99/p55 latency tracking

### 3. Production Node Layer
- Node identity
- Storage path management
- Node-level health/status reporting
- Integration with ingestion and core layers

## Key Features

- Distributed memory substrate
- Importance-based retention
- Tiered storage model
- Vector-based scoring
- Drift-aware decay
- High-cardinality ingestion
- Horizontal scalability
- Low-latency retrieval

## Installation

git clone https://github.com/tpappy83/Helios-Memory-Substrate-1.1
cd Helios-Memory-Substrate-1.1

## Usage Example

from production_node import HeliosProductionNode

node = HeliosProductionNode(node_id="node-1", storage_path="./data")
print(node.get_status())

## Contributing

See CONTRIBUTING.md for full guidelines.

## Security

See SECURITY.md for vulnerability reporting instructions.

## Roadmap

See ROADMAP.md for planned milestones.

## License

Apache 2.0 — you retain 100 percent ownership.
## Testing

Helios Memory Substrate uses pytest for testing.

### Running the Test Suite

1. Install dependencies:
   pip install -r requirements.txt

2. Run all tests:
   pytest -v

3. Run a specific test file:
   pytest tests/test_production_node.py

4. Generate a coverage report:
   pytest --cov=.

### Test Directory Structure

tests/
├── test_helios_core.py
├── test_production_node.py
└── test_quark_ingest.py

## Contributing and Collaboration

Contributions are welcome and encouraged. To contribute:

1. Fork the repository.
2. Create a feature branch:
   git checkout -b feature/my-feature
3. Commit your changes with clear messages.
4. Push your branch:
   git push origin feature/my-feature
5. Open a Pull Request.

### Collaboration Guidelines

- Use Issues to report bugs or request features.
- Use Discussions for architectural questions or design proposals.
- Follow the coding style and testing requirements in CONTRIBUTING.md.
- Be respectful and constructive in all interactions.

### Communication

For questions or collaboration proposals, contact:
tpapenb@iu.edu
