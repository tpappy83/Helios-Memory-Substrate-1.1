
import os
from helios_core import HeliosDistributedCore
from quark_ingest import QuarkIngestionAgent

class HeliosProductionNode:
    def __init__(self, node_id: str, storage_path: str):
        self.node_id = node_id
        self.core = HeliosDistributedCore()
        self.ingestor = QuarkIngestionAgent()
        self.storage_path = storage_path

    def get_status(self):
        return {
            "node_id": self.node_id,
            "status": "ACTIVE",
            "storage": self.storage_path
        }

if __name__ == '__main__':
    # Example local initialization
    node = HeliosProductionNode(node_id='node-01', storage_path='./data')
    print(f'Helios Node {node.node_id} is now running.')
