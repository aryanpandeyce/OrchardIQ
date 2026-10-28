"""Near-real-time transactional event streaming pipeline simulator for OrchardIQ."""

import random
import time
import uuid
from typing import Dict, List, Any, Generator, Optional
from dataclasses import dataclass, asdict


@dataclass
class StreamEvent:
    """Real-time transaction or defect event."""
    id: str
    timestamp: str
    epoch_time: float
    eventType: str  # "SALE", "CLAIM", "RETURN", "ATTACH"
    product: str
    product_id: str
    region: str
    amount: str
    amount_usd: float
    customer_masked: str
    store_name: str
    badgeColor: str


class TransactionStreamSimulator:
    """Simulates near-real-time streaming transaction pipeline feeding live dashboard tiles."""

    PRODUCTS = [
        ("PRD-PHN-16P", "PearPhone 16 Pro", 1199.00),
        ("PRD-NBK-16P", "PearBook Pro 16\"", 2499.00),
        ("PRD-WCH-ULT2", "PearWatch Ultra 2", 799.00),
        ("PRD-AUD-PRO2", "PearBuds Pro", 249.00),
        ("PRD-TAB-AIR", "PearPad Air 11\"", 599.00),
    ]

    REGIONS = ["AMER", "EMEA", "APAC", "LATAM"]

    STORES = [
        "Orchard Fifth Avenue",
        "Orchard Regent Street",
        "Orchard Ginza",
        "Orchard Online Store",
        "Orchard Champs-Élysées",
        "Orchard Sydney",
    ]

    def __init__(self, buffer_size: int = 100):
        self.buffer_size = buffer_size
        self._recent_events: List[StreamEvent] = []
        # Pre-populate with initial events
        for _ in range(10):
            self.generate_event()

    def generate_event(self) -> StreamEvent:
        """Generate a single random realistic business event."""
        p_id, p_name, base_price = random.choice(self.PRODUCTS)
        region = random.choice(self.REGIONS)
        store = random.choice(self.STORES)

        # Weighted event distribution: 70% Sales/Attach, 15% Claims, 15% Returns
        r = random.random()
        if r < 0.55:
            e_type = "SALE"
            amt_val = round(base_price * random.choice([1, 1, 2]), 2)
            badge = "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
        elif r < 0.75:
            e_type = "ATTACH"
            amt_val = round(base_price + 799.00, 2)
            badge = "bg-cyan-500/10 text-cyan-400 border-cyan-500/30"
        elif r < 0.90:
            e_type = "CLAIM"
            amt_val = round(random.uniform(89.0, 350.0), 2)
            badge = "bg-rose-500/10 text-rose-400 border-rose-500/30"
        else:
            e_type = "RETURN"
            amt_val = round(base_price, 2)
            badge = "bg-amber-500/10 text-amber-400 border-amber-500/30"

        now = time.time()
        evt = StreamEvent(
            id=f"EVT-{uuid.uuid4().hex[:6].upper()}",
            timestamp=time.strftime("%H:%M:%S", time.localtime(now)),
            epoch_time=now,
            eventType=e_type,
            product=p_name,
            product_id=p_id,
            region=region,
            amount=f"${amt_val:,.2f}",
            amount_usd=amt_val,
            customer_masked=f"USR-{uuid.uuid4().hex[:4].upper()}***@privaterelay.orchard.com",
            store_name=store,
            badgeColor=badge,
        )

        self._recent_events.insert(0, evt)
        if len(self._recent_events) > self.buffer_size:
            self._recent_events.pop()

        return evt

    def get_recent_events(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Return the most recent events from the stream buffer."""
        return [asdict(e) for e in self._recent_events[:limit]]

    def stream_generator(self, interval_sec: float = 1.0, count: Optional[int] = None) -> Generator[Dict[str, Any], None, None]:
        """Generator yielding simulated live events at regular intervals."""
        yielded = 0
        while count is None or yielded < count:
            evt = self.generate_event()
            yield asdict(evt)
            yielded += 1
            time.sleep(interval_sec)


stream_simulator = TransactionStreamSimulator()
