# logger.py
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import json

class WorkflowLogger:
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self._setup_logging()

    def _setup_logging(self):
        log_file = self.log_dir / f"workflow_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger("workflow")

    def log(self, level: str, message: str, extra: Dict[str, Any] = None):
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(message, extra=extra or {})

    def log_incident(self, ticket_id: str, action: str, details: Dict[str, Any]):
        self.log("INFO", f"Incident {action}", {
            "ticket_id": ticket_id,
            "details": json.dumps(details)
        })