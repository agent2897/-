from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional
import uuid


@dataclass
class Detainee:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    full_name: str = ""
    birth_date: Optional[datetime] = None
    gender: str = ""
    document_number: str = ""
    address: str = ""
    case_number: str = ""
    barcode: str = ""
    status: str = "active"
    detention: Optional[DetentionRecord] = None
    items: List[StoredItem] = field(default_factory=list)

    def generate_barcode(self) -> str:
        self.barcode = f"{self.case_number}-{self.id.hex[:8]}"
        return self.barcode


@dataclass
class DetentionRecord:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    protocol_number: str = ""
    article: str = ""
    arrival_time: datetime = field(default_factory=datetime.now)
    deadline: Optional[datetime] = None
    status: str = "active"
    release_reason: str = ""

    def calculate_deadline(self, hours: int) -> datetime:
        self.deadline = self.arrival_time + timedelta(hours=hours)
        return self.deadline

    def extend(self, decision_number: str, new_deadline: datetime) -> bool:
        if not decision_number or new_deadline <= datetime.now() or new_deadline - datetime.now() > timedelta(hours=72):
            return False
        self.deadline = new_deadline
        self.release_reason = decision_number
        return True

    def is_expired(self) -> bool:
        return self.deadline is not None and datetime.now() >= self.deadline

    def indicator(self) -> str:
        if self.deadline is None:
            return "unknown"
        remaining = self.deadline - datetime.now()
        if remaining.total_seconds() <= 0:
            return "red"
        if remaining.total_seconds() < 3600:
            return "red"
        if remaining.total_seconds() < 6 * 3600:
            return "yellow"
        return "green"


@dataclass
class StoredItem:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    name: str = ""
    description: str = ""
    returned: bool = False


@dataclass
class Document:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    document_type: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    signed: bool = False
    file_path: str = ""

    def save_pdf(self) -> None:
        self.file_path = f"documents/{self.id.hex}_{self.document_type}.pdf"


@dataclass
class Actor:
    name: str = ""
    role: str = ""


@dataclass
class AuditEntry:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    action: str = ""
    user: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    details: str = ""
