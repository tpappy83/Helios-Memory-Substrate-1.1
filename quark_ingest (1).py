
import uuid
from datetime import datetime

class QuarkIngestionAgent:
    def __init__(self, window=60):
        self.window = window
        self.batch = []

    def process(self, data, origin):
        meta = {'id': str(uuid.uuid4()), 'ts': datetime.now().isoformat()}
        self.batch.append({'data': data, 'meta': meta})
        return len(self.batch)
