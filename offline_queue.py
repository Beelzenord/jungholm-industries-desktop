"""Offline event queue with retry mechanism"""
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Callable
from datetime import datetime
from config import OFFLINE_QUEUE_FILE, MAX_RETRY_ATTEMPTS, RETRY_BACKOFF_BASE

logger = logging.getLogger(__name__)


class OfflineQueue:
    """Manages offline event queue with exponential backoff retry"""
    
    def __init__(self):
        self.queue_file = OFFLINE_QUEUE_FILE
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_queue()
    
    def _load_queue(self):
        """Load queue from disk"""
        if self.queue_file.exists():
            try:
                with open(self.queue_file, 'r') as f:
                    self.queue = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load queue: {e}")
                self.queue = []
        else:
            self.queue = []
    
    def _save_queue(self):
        """Save queue to disk"""
        try:
            with open(self.queue_file, 'w') as f:
                json.dump(self.queue, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save queue: {e}")
    
    def add_event(self, event_type: str, data: Dict[str, Any]):
        """Add an event to the queue"""
        event = {
            "type": event_type,
            "data": data,
            "created_at": datetime.utcnow().isoformat(),
            "attempts": 0,
            "last_attempt": None
        }
        self.queue.append(event)
        self._save_queue()
        logger.info(f"Added event to queue: {event_type}")
    
    def get_pending_events(self) -> List[Dict[str, Any]]:
        """Get events that are ready to retry"""
        now = time.time()
        ready_events = []
        
        for event in self.queue:
            attempts = event.get("attempts", 0)
            if attempts >= MAX_RETRY_ATTEMPTS:
                continue  # Skip maxed out events
            
            last_attempt = event.get("last_attempt")
            if last_attempt:
                # Calculate backoff delay
                delay = RETRY_BACKOFF_BASE ** attempts
                last_attempt_time = datetime.fromisoformat(last_attempt).timestamp()
                if now - last_attempt_time < delay:
                    continue  # Not ready yet
            
            ready_events.append(event)
        
        return ready_events
    
    def mark_attempt(self, event: Dict[str, Any], success: bool):
        """Mark an event as attempted"""
        if success:
            # Remove from queue on success
            if event in self.queue:
                self.queue.remove(event)
                self._save_queue()
                logger.info(f"Successfully processed event: {event['type']}")
        else:
            # Increment attempts
            event["attempts"] = event.get("attempts", 0) + 1
            event["last_attempt"] = datetime.utcnow().isoformat()
            self._save_queue()
            logger.warning(f"Failed to process event: {event['type']}, attempts: {event['attempts']}")
    
    def process_queue(self, processor: Callable[[Dict[str, Any]], bool]):
        """Process all ready events in the queue"""
        pending = self.get_pending_events()
        processed = 0
        
        for event in pending:
            try:
                success = processor(event)
                self.mark_attempt(event, success)
                if success:
                    processed += 1
            except Exception as e:
                logger.error(f"Error processing event: {e}")
                self.mark_attempt(event, False)
        
        return processed
    
    def clear_failed_events(self):
        """Clear events that have exceeded max retry attempts"""
        initial_count = len(self.queue)
        self.queue = [e for e in self.queue if e.get("attempts", 0) < MAX_RETRY_ATTEMPTS]
        removed = initial_count - len(self.queue)
        if removed > 0:
            self._save_queue()
            logger.info(f"Cleared {removed} failed events")
        return removed

