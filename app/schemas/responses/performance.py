from pydantic import BaseModel


class PerformanceResponse(BaseModel):
    latency_ms: float
    memory_mb: float
    threads_used: int