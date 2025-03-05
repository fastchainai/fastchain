"""Metrics endpoint implementation."""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from src.utils.metrics import Metrics

router = APIRouter()

@router.get("/", response_model=Dict[str, Any])
async def get_metrics():
    """Return all collected metrics from the unified Metrics module."""
    try:
        # Initialize metrics collector with service name
        metrics = Metrics("api_metrics")
        
        # Get metrics data from store
        metrics_data = metrics.store.get_metrics()
        
        # Format response
        response = {
            "metrics": metrics_data,
            "collectors": {
                "counters": len([m for m in metrics_data if m.get("type") == "counter"]),
                "gauges": len([m for m in metrics_data if m.get("type") == "gauge"]),
                "histograms": len([m for m in metrics_data if m.get("type") == "histogram"])
            }
        }
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to collect metrics: {str(e)}")
