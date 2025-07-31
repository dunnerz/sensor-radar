"""
Progress store for tracking computation progress.
This module provides a centralized way to manage progress tracking
without creating circular imports.
"""

from typing import Dict, Any
import threading
import time

# Global progress store with thread safety
_progress_store: Dict[str, Dict[str, Any]] = {}
_progress_lock = threading.Lock()

# OPTIMIZATION: Auto-cleanup configuration
MAX_COMPLETED_JOBS = 100  # Maximum number of completed jobs to keep in memory
CLEANUP_INTERVAL = 300  # Cleanup every 5 minutes

def get_progress_store() -> Dict[str, Dict[str, Any]]:
    """Get the global progress store."""
    return _progress_store

def update_progress(job_id: str, updates: Dict[str, Any]) -> None:
    """Update progress for a specific job."""
    with _progress_lock:
        if job_id in _progress_store:
            _progress_store[job_id].update(updates)
            # OPTIMIZATION: Auto-cleanup completed jobs
            if updates.get('status') in ['completed', 'error']:
                _cleanup_old_jobs()

def get_progress(job_id: str) -> Dict[str, Any]:
    """Get progress for a specific job."""
    with _progress_lock:
        return _progress_store.get(job_id, {})

def set_progress(job_id: str, progress_data: Dict[str, Any]) -> None:
    """Set progress for a specific job."""
    with _progress_lock:
        _progress_store[job_id] = progress_data

def remove_progress(job_id: str) -> None:
    """Remove progress for a specific job."""
    with _progress_lock:
        if job_id in _progress_store:
            del _progress_store[job_id]

def get_active_jobs_count() -> int:
    """Get the number of active jobs."""
    with _progress_lock:
        return len(_progress_store)

def _cleanup_old_jobs():
    """OPTIMIZATION: Remove old completed jobs to prevent memory leaks."""
    current_time = time.time()
    completed_jobs = []
    
    # Find completed jobs older than cleanup interval
    for job_id, job_data in _progress_store.items():
        if job_data.get('status') in ['completed', 'error']:
            completed_jobs.append(job_id)
    
    # Remove oldest completed jobs if we have too many
    if len(completed_jobs) > MAX_COMPLETED_JOBS:
        # Remove oldest jobs first
        for job_id in completed_jobs[:-MAX_COMPLETED_JOBS]:
            del _progress_store[job_id] 