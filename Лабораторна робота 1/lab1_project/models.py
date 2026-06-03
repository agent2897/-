from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, date
from typing import List, Optional
import uuid


@dataclass
class Detainee:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    full_name: str = ""
    birth_date: Optional[date] = None
    gender: str = ""
    document_number: str = ""
    address: str = ""
    photo_path: str = ""
    case_number: str = ""
    barcode: str = ""
    health_status: str = ""
    detentions: List[DetentionRecord] = field(default_factory=list)

    def is_duplicate_of(self, other: "Detainee") -> bool:
        return self.full_name == other.full_name and self.birth_date == other.birth_date

    def register_detention(self, detention: DetentionRecord) -> None:
        self.detentions.append(detention)

    def current_detention(self) -> Optional[DetentionRecord]:
        return self.detentions[-1] if self.detentions else None

    def generate_barcode(self) -> str:
        self.barcode = f"{self.case_number}-{self.id.hex[:8]}"
        return self.barcode


@dataclass
class DetentionRecord:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    protocol_number: str = ""
    article: str = ""
    division: str = ""
    arrival_time: datetime = field(default_factory=datetime.now)
    legal_deadline: Optional[datetime] = None
    status: str = "active"
    cell_id: Optional[int] = None
    extension_reason: str = ""
    release_time: Optional[datetime] = None

    def calculate_deadline(self, hours: int) -> datetime:
        self.legal_deadline = self.arrival_time + timedelta(hours=hours)
        return self.legal_deadline

    def remaining_seconds(self) -> int:
        if not self.legal_deadline:
            return 0
        delta = self.legal_deadline - datetime.now()
        return max(int(delta.total_seconds()), 0)

    def deadline_indicator(self) -> str:
        if not self.legal_deadline:
            return "unknown"
        remaining = self.legal_deadline - datetime.now()
        if remaining.total_seconds() <= 0:
            return "red"
        if remaining.total_seconds() < 3600:
            return "red"
        if remaining.total_seconds() < 6 * 3600:
            return "yellow"
        return "green"

    def extend_deadline(self, decision_number: str, new_deadline: datetime) -> bool:
        if not decision_number or new_deadline <= datetime.now() or new_deadline - datetime.now() > timedelta(hours=72):
            return False
        self.legal_deadline = new_deadline
        self.extension_reason = decision_number
        return True

    def release(self) -> None:
        self.release_time = datetime.now()
        self.status = "released"


@dataclass
class Cell:
    id: int
    number: str
    capacity: int
    gender_type: str
    is_medical: bool
    occupancy: int = 0

    def is_available(self) -> bool:
        return self.occupancy < self.capacity

    def assign(self) -> bool:
        if self.is_available():
            self.occupancy += 1
            return True
        return False

    def release(self) -> None:
        self.occupancy = max(self.occupancy - 1, 0)


@dataclass
class Event:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    detention_id: uuid.UUID = field(default_factory=uuid.uuid4)
    event_type: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    description: str = ""
    participant: str = ""


@dataclass
class Document:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    document_type: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    file_path: str = ""
    is_signed: bool = False

    def generate_pdf(self) -> None:
        self.file_path = f"documents/{self.id.hex}_{self.document_type}.pdf"

    def sign(self) -> None:
        self.is_signed = True


@dataclass
class User:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    username: str = ""
    password_hash: str = ""
    full_name: str = ""
    role: str = ""

    def can_access(self, permission: str) -> bool:
        return self.role.lower() in ("черговий", "начальник зміни", "медичний персонал", "адміністратор")


@dataclass
class AuditLog:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    action: str = ""
    target_table: str = ""
    old_values: str = ""
    new_values: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    ip_address: str = "127.0.0.1"


@dataclass
class SystemState:
    detainees: List[Detainee] = field(default_factory=list)
    cells: List[Cell] = field(default_factory=list)
    events: List[Event] = field(default_factory=list)
    documents: List[Document] = field(default_factory=list)
    audit_logs: List[AuditLog] = field(default_factory=list)

    def find_duplicate(self, candidate: Detainee) -> Optional[Detainee]:
        for detainee in self.detainees:
            if detainee.is_duplicate_of(candidate):
                return detainee
        return None

    def register_detainee(self, detainee: Detainee, detention: DetentionRecord) -> str:
        duplicate = self.find_duplicate(detainee)
        if duplicate:
            return f"duplicate found: {duplicate.full_name}"
        detainee.generate_barcode()
        detainee.register_detention(detention)
        self.detainees.append(detainee)
        self.documents.append(Document(document_type="RegistrationCard"))
        return "registered"

    def assign_cell(self, detention: DetentionRecord, cell: Cell) -> bool:
        if cell.gender_type.lower() != detainee_gender(detention):
            return False
        if not cell.is_available():
            return False
        cell.assign()
        detention.cell_id = cell.id
        return True


def detainee_gender(detention: DetentionRecord) -> str:
    return "male" if detention.article else "male"
