"""OpenTelemetry-style structured tracing subsystem for multi-agent workflows."""

import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from contextlib import contextmanager


@dataclass
class Span:
    """An individual operation span within an execution trace."""
    span_id: str
    trace_id: str
    name: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: float = 0.0
    status: str = "OK"
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)

    def finish(self, status: str = "OK"):
        """Mark span as finished and compute duration."""
        self.end_time = time.time()
        self.duration_ms = round((self.end_time - self.start_time) * 1000, 2)
        self.status = status

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Record a timestamped event within the span."""
        self.events.append({
            "name": name,
            "timestamp": time.time(),
            "attributes": attributes or {},
        })

    def to_dict(self) -> Dict[str, Any]:
        """Serialize span to dictionary."""
        return {
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "span_name": self.name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "attributes": self.attributes,
            "events": self.events,
        }


@dataclass
class Trace:
    """Structured collection of spans representing a full query lifecycle."""
    trace_id: str
    run_id: str
    user_query: str
    role: str
    start_time: float
    end_time: Optional[float] = None
    total_duration_ms: float = 0.0
    spans: List[Span] = field(default_factory=list)
    status: str = "RUNNING"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def finish(self, status: str = "COMPLETED"):
        self.end_time = time.time()
        self.total_duration_ms = round((self.end_time - self.start_time) * 1000, 2)
        self.status = status

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "run_id": self.run_id,
            "user_query": self.user_query,
            "role": self.role,
            "trace_status": self.status,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "total_latency_ms": self.total_duration_ms,
            "spans": [s.to_dict() for s in self.spans],
            "metadata": self.metadata,
        }


class OrchardTracer:
    """Central registry managing active and past traces."""

    def __init__(self, max_retained_traces: int = 1000):
        self._traces: Dict[str, Trace] = {}  # run_id -> Trace
        self._max_retained = max_retained_traces

    def start_trace(self, run_id: str, query: str = "", role: str = "analyst") -> Trace:
        """Create and register a new execution trace."""
        trace_id = f"trc_{uuid.uuid4().hex[:12]}"
        trace = Trace(
            trace_id=trace_id,
            run_id=run_id,
            user_query=query,
            role=role,
            start_time=time.time(),
        )
        if len(self._traces) >= self._max_retained:
            oldest_key = next(iter(self._traces))
            del self._traces[oldest_key]
        self._traces[run_id] = trace
        return trace

    def get_trace(self, run_id: str) -> Optional[Trace]:
        """Lookup a trace by run_id."""
        return self._traces.get(run_id)

    @contextmanager
    def span(self, run_id: str, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Context manager to measure span execution time and record in trace."""
        trace = self._traces.get(run_id)
        if not trace:
            trace = self.start_trace(run_id)

        span_id = f"spn_{uuid.uuid4().hex[:8]}"
        s = Span(
            span_id=span_id,
            trace_id=trace.trace_id,
            name=name,
            start_time=time.time(),
            attributes=attributes or {},
        )
        trace.spans.append(s)
        try:
            yield s
            s.finish("OK")
        except Exception as e:
            s.finish("ERROR")
            s.add_event("exception", {"error": str(e)})
            raise


tracer = OrchardTracer()
