"""
Database Polling Service for Analytics Requests

This service runs as part of the main application and continuously polls
the database for analytics requests to process. It can resume from failures
and handle interrupted requests gracefully.
"""

import asyncio
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Optional, Set
import atexit

from .database import DatabaseManager
from .analytics_engine import process_analytics_request_async

logger = logging.getLogger(__name__)


class AnalyticsPollingService:
    """Database polling service for processing analytics requests"""
    
    _instance: Optional['AnalyticsPollingService'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern to ensure only one service instance"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the polling service"""
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.poll_interval = 10  # seconds between polls
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.processing_requests: Set[int] = set()
        self.db_manager: Optional[DatabaseManager] = None
        
        # Register cleanup on application exit
        atexit.register(self.stop)
        
        logger.info("Analytics Polling Service initialized")
    
    async def _initialize_database(self):
        """Initialize database connection"""
        if self.db_manager is None:
            self.db_manager = DatabaseManager()
            await self.db_manager.initialize()
            logger.info("Polling service database connection initialized")
    
    async def _resume_interrupted_requests(self):
        """Resume requests that were interrupted during previous run"""
        try:
            # Find requests that were "Running" but might have been interrupted
            running_requests = await self.db_manager.get_analytics_requests("Running")
            
            for request in running_requests:
                if request.started_date:
                    # If request has been running for more than 5 minutes without progress,
                    # consider it interrupted and reset to "Requested"
                    time_running = datetime.utcnow() - request.started_date
                    if time_running > timedelta(minutes=5):
                        logger.warning(
                            f"Request #{request.id} appears to have been interrupted "
                            f"(running for {time_running}). Resetting to 'Requested' status."
                        )
                        await self.db_manager.update_request_status(
                            request.id, 
                            "Requested",
                            error_message=None  # Clear any previous error
                        )
            
            logger.info("Completed check for interrupted requests")
            
        except Exception as e:
            logger.error(f"Error checking for interrupted requests: {e}")
    
    async def _poll_and_process(self):
        """Main polling loop - checks for and processes pending requests"""
        try:
            await self._initialize_database()
            await self._resume_interrupted_requests()
            
            while self.running:
                try:
                    # Get pending requests
                    pending_requests = await self.db_manager.get_analytics_requests("Requested")
                    
                    for request in pending_requests:
                        if not self.running:
                            break
                        
                        # Skip if already processing this request
                        if request.id in self.processing_requests:
                            continue
                        
                        # Start processing this request
                        self.processing_requests.add(request.id)
                        logger.info(f"Starting to process request #{request.id} for project '{request.project_name}'")
                        
                        try:
                            # Process the request
                            await process_analytics_request_async(request.id)
                            logger.info(f"Successfully completed request #{request.id}")
                            
                        except Exception as e:
                            logger.error(f"Failed to process request #{request.id}: {e}")
                            # Error handling is done in process_analytics_request_async
                        
                        finally:
                            # Remove from processing set
                            self.processing_requests.discard(request.id)
                    
                    # Wait before next poll
                    for _ in range(self.poll_interval):
                        if not self.running:
                            break
                        await asyncio.sleep(1)
                
                except Exception as e:
                    logger.error(f"Error in polling loop: {e}")
                    await asyncio.sleep(5)  # Wait a bit before retrying
            
        except Exception as e:
            logger.error(f"Fatal error in polling service: {e}")
        finally:
            if self.db_manager:
                await self.db_manager.close()
            logger.info("Polling service stopped")
    
    def _run_polling_loop(self):
        """Run the polling loop in an async context"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._poll_and_process())
        except Exception as e:
            logger.error(f"Polling thread error: {e}")
        finally:
            try:
                loop.close()
            except:
                pass
    
    def start(self):
        """Start the polling service"""
        if self.running:
            logger.warning("Polling service is already running")
            return
        
        self.running = True
        self.thread = threading.Thread(
            target=self._run_polling_loop,
            daemon=True,
            name="analytics-polling-service"
        )
        self.thread.start()
        logger.info("Analytics Polling Service started")
    
    def stop(self):
        """Stop the polling service"""
        if not self.running:
            return
        
        logger.info("Stopping Analytics Polling Service...")
        self.running = False
        
        if self.thread and self.thread.is_alive():
            # Give the thread time to finish current operation
            self.thread.join(timeout=10)
            if self.thread.is_alive():
                logger.warning("Polling service thread did not stop gracefully")
        
        logger.info("Analytics Polling Service stopped")
    
    def is_running(self) -> bool:
        """Check if the service is running"""
        return self.running and self.thread and self.thread.is_alive()
    
    def get_status(self) -> dict:
        """Get service status information"""
        return {
            "running": self.is_running(),
            "processing_count": len(self.processing_requests),
            "processing_requests": list(self.processing_requests),
            "poll_interval": self.poll_interval
        }


# Global service instance
_service_instance: Optional[AnalyticsPollingService] = None


def get_polling_service() -> AnalyticsPollingService:
    """Get the global polling service instance"""
    global _service_instance
    if _service_instance is None:
        _service_instance = AnalyticsPollingService()
    return _service_instance


def start_polling_service():
    """Start the global polling service"""
    service = get_polling_service()
    service.start()
    return service


def stop_polling_service():
    """Stop the global polling service"""
    service = get_polling_service()
    service.stop()


def is_polling_service_running() -> bool:
    """Check if the polling service is running"""
    service = get_polling_service()
    return service.is_running() 