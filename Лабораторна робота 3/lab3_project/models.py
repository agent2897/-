from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, time
from typing import List, Optional
import uuid


@dataclass
class Person(ABC):
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    last_name: str = ""
    first_name: str = ""
    middle_name: str = ""
    birth_date: Optional[date] = None
    gender: str = ""
    document_number: str = ""
    address: str = ""

    def get_full_name(self) -> str:
        return f"{self.last_name} {self.first_name} {self.middle_name}".strip()

    def get_age(self) -> int:
        if not self.birth_date:
            return 0
        today = date.today()
        age = today.year - self.birth_date.year
        if (today.month, today.day) < (self.birth_date.month, self.birth_date.day):
            age -= 1
        return age

    def validate_document(self) -> bool:
        return bool(self.document_number and len(self.document_number) >= 5)

    def get_document_info(self) -> str:
        return f"Document: {self.document_number}"

    def update_address(self, address: str) -> None:
        self.address = address


@dataclass
class Detainee(Person):
    case_number: str = ""
    photo_path: str = ""
    health_notes: str = ""
    special_marks: str = ""
    current_status: str = ""
    detentions: List[DetentionRecord] = field(default_factory=list)

    def register(self, record: DetentionRecord) -> None:
        self.detentions.append(record)

    def get_current_detention(self) -> Optional[DetentionRecord]:
        return self.detentions[-1] if self.detentions else None

    def get_detention_history(self) -> List[DetentionRecord]:
        return list(self.detentions)

    def generate_barcode(self) -> str:
        return f"{self.case_number}-{self.id.hex[:8]}"

    def update_health_notes(self, notes: str) -> None:
        self.health_notes = notes


@dataclass
class Staff(Person, ABC):
    employee_id: str = ""
    username: str = ""
    password_hash: str = ""
    role: str = ""
    is_active: bool = True

    def login(self, username: str, password: str) -> bool:
        return self.username == username and self.password_hash == password

    def logout(self) -> None:
        self.is_active = False

    def change_password(self, old: str, new: str) -> bool:
        if self.password_hash == old:
            self.password_hash = new
            return True
        return False

    def get_role(self) -> str:
        return self.role

    def check_permission(self, action: str) -> bool:
        return self.role.lower() in ("admin", "dutyofficer", "medicalstaff")


@dataclass
class DutyOfficer(Staff):
    shift_start: Optional[datetime] = None
    shift_end: Optional[datetime] = None
    is_on_shift: bool = False
    badge_number: str = ""
    supervisor_id: Optional[uuid.UUID] = None

    def start_shift(self) -> None:
        self.shift_start = datetime.now()
        self.is_on_shift = True

    def end_shift(self) -> None:
        self.shift_end = datetime.now()
        self.is_on_shift = False

    def register_detainee(self, detainee: Detainee, record: DetentionRecord) -> None:
        detainee.register(record)

    def process_release(self, record: DetentionRecord) -> None:
        record.release("Released by officer")

    def add_event(self, event: Event) -> None:
        event.register(record=event.detention_record)


@dataclass
class MedicalStaff(Staff):
    license_number: str = ""
    specialization: str = ""
    available_from: Optional[time] = None
    available_to: Optional[time] = None
    qualification: str = ""

    def conduct_examination(self, detainee: Detainee) -> Event:
        return Event(
            detention_record=detainee.get_current_detention(),
            event_type="Medical Examination",
            description="Routine examination",
            participant_name=self.get_full_name(),
        )

    def update_health_record(self, detainee: Detainee, notes: str) -> None:
        detainee.update_health_notes(notes)

    def prescribe_treatment(self, detainee: Detainee, treatment: str) -> None:
        pass

    def check_medical_history(self, detainee: Detainee) -> str:
        return detainee.health_notes

    def issue_health_certificate(self, detainee: Detainee) -> Document:
        doc = Document(document_type="HealthCertificate", created_by=self.id)
        doc.generate(detainee.get_current_detention())
        return doc


@dataclass
class DetentionRecord:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    protocol_number: str = ""
    article: str = ""
    arrival_time: datetime = field(default_factory=datetime.now)
    legal_deadline: Optional[datetime] = None
    release_time: Optional[datetime] = None
    status: str = "Active"
    events: List[Event] = field(default_factory=list)
    properties: List[StoredProperty] = field(default_factory=list)
    documents: List[Document] = field(default_factory=list)

    def calculate_deadline(self, hours: int) -> datetime:
        self.legal_deadline = self.arrival_time + timedelta(hours=hours)
        return self.legal_deadline

    def get_remaining_time(self) -> timedelta:
        if not self.legal_deadline:
            return timedelta(0)
        return max(self.legal_deadline - datetime.now(), timedelta(0))

    def extend_detention(self, reason: str, new_deadline: datetime) -> None:
        self.legal_deadline = new_deadline
        self.status = f"Extended: {reason}"

    def release(self, reason: str) -> None:
        self.release_time = datetime.now()
        self.status = f"Released: {reason}"

    def transfer(self, destination: str) -> None:
        self.status = f"Transferred to {destination}"


@dataclass
class Cell:
    id: int
    cell_number: str
    capacity: int
    gender_type: str
    is_medical: bool
    current_occupancy: int = 0
    assignments: List[CellAssignment] = field(default_factory=list)

    def get_current_occupants(self) -> List[CellAssignment]:
        return [assignment for assignment in self.assignments if assignment.is_active()]

    def is_available(self) -> bool:
        return self.current_occupancy < self.capacity

    def get_occupancy_rate(self) -> float:
        return self.current_occupancy / self.capacity if self.capacity else 0.0

    def add_detainee(self, assignment: CellAssignment) -> None:
        if self.is_available():
            self.assignments.append(assignment)
            self.current_occupancy += 1

    def remove_detainee(self, detainee_id: uuid.UUID) -> None:
        for assignment in self.assignments:
            if assignment.detention_id == detainee_id and assignment.is_active():
                assignment.remove("Released from cell")
                self.current_occupancy = max(0, self.current_occupancy - 1)
                break


@dataclass
class CellAssignment:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    detention_id: uuid.UUID = field(default_factory=uuid.uuid4)
    cell_id: int = 0
    assigned_at: datetime = field(default_factory=datetime.now)
    removed_at: Optional[datetime] = None
    transfer_reason: str = ""
    detention_record: Optional[DetentionRecord] = None

    def assign(self, cell: Cell, record: DetentionRecord) -> None:
        self.cell_id = cell.id
        self.detention_record = record
        self.detention_id = record.id
        cell.add_detainee(self)

    def remove(self, reason: str) -> None:
        self.removed_at = datetime.now()
        self.transfer_reason = reason

    def get_duration(self) -> timedelta:
        end_time = self.removed_at or datetime.now()
        return end_time - self.assigned_at

    def is_active(self) -> bool:
        return self.removed_at is None

    def get_history(self) -> List[CellAssignment]:
        return [self]


@dataclass
class Event:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    detention_record: Optional[DetentionRecord] = None
    event_type: str = ""
    event_time: datetime = field(default_factory=datetime.now)
    description: str = ""
    participant_name: str = ""

    def register(self, record: DetentionRecord) -> None:
        self.detention_record = record
        record.events.append(self)

    def get_details(self) -> str:
        return f"{self.event_type} at {self.event_time}: {self.description}"

    def validate(self) -> bool:
        return bool(self.event_type and self.detention_record)

    def generate_report(self) -> Document:
        report = Document(document_type="EventReport", created_by=self.detention_record.id if self.detention_record else uuid.uuid4())
        report.generate(self.detention_record)
        return report

    def get_participant_info(self) -> str:
        return self.participant_name


@dataclass
class Document:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    document_type: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    created_by: uuid.UUID = field(default_factory=uuid.uuid4)
    file_path: str = ""
    is_signed: bool = False

    def generate(self, record: Optional[DetentionRecord] = None) -> None:
        if record:
            self.file_path = f"documents/{record.id.hex}_{self.document_type}.pdf"

    def print(self) -> None:
        pass

    def save_to_pdf(self) -> None:
        pass

    def sign(self, officer: Staff) -> None:
        self.is_signed = True
        self.created_by = officer.id

    def archive(self) -> None:
        pass


@dataclass
class StoredProperty:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    detention_id: uuid.UUID = field(default_factory=uuid.uuid4)
    item_name: str = ""
    description: str = ""
    stored_at: datetime = field(default_factory=datetime.now)
    is_returned: bool = False

    def confiscate(self, record: DetentionRecord) -> None:
        self.detention_id = record.id

    def return_to_owner(self, officer: DutyOfficer) -> None:
        self.is_returned = True

    def generate_receipt(self, officer: DutyOfficer) -> Document:
        doc = Document(document_type="PropertyReceipt", created_by=officer.id)
        doc.generate(None)
        return doc

    def get_storage_info(self) -> str:
        return f"Stored at {self.stored_at.isoformat()}"

    def update_description(self, desc: str) -> None:
        self.description = desc


@dataclass
class AuditLog:
    id: int
    user_id: uuid.UUID
    action: str
    table_name: str
    old_values: str
    performed_at: datetime = field(default_factory=datetime.now)
    ip_address: str = ""

    @staticmethod
    def log_action(user: Staff, action: str) -> "AuditLog":
        return AuditLog(
            id=0,
            user_id=user.id,
            action=action,
            table_name="System",
            old_values="",
            ip_address="127.0.0.1",
        )

    @staticmethod
    def get_logs_by_user(user_id: uuid.UUID, logs: List["AuditLog"]) -> List["AuditLog"]:
        return [log for log in logs if log.user_id == user_id]

    @staticmethod
    def get_logs_by_date(from_date: datetime, to_date: datetime, logs: List["AuditLog"]) -> List["AuditLog"]:
        return [log for log in logs if from_date <= log.performed_at <= to_date]

    def export_to_excel(self) -> None:
        pass

    def search_logs(self, query: str) -> List["AuditLog"]:
        return [self] if query in self.action else []


class NotificationService(ABC):
    alert_threshold_hours: int = 24
    sound_enabled: bool = True
    repeat_interval: int = 60
    max_alerts_per_hour: int = 5
    notification_log: List[str] = []

    @abstractmethod
    def send_alert(self, record: DetentionRecord) -> None:
        pass

    @abstractmethod
    def check_deadlines(self) -> None:
        pass

    @abstractmethod
    def schedule_reminder(self, record: DetentionRecord, delay: int) -> None:
        pass

    @abstractmethod
    def cancel_reminder(self, reminder_id: uuid.UUID) -> None:
        pass

    @abstractmethod
    def get_active_alerts(self) -> List[str]:
        pass


class ReportGenerator(NotificationService):
    report_type: str = ""
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    output_format: str = "PDF"
    template_path: str = ""

    def generate_statistics(self, from_date: date, to_date: date) -> Document:
        doc = Document(document_type="StatisticsReport", created_by=uuid.uuid4())
        doc.generate(None)
        return doc

    def generate_detainee_card(self, detainee: Detainee) -> Document:
        doc = Document(document_type="DetaineeCard", created_by=detainee.id)
        doc.generate(detainee.get_current_detention())
        return doc

    def generate_release_act(self, record: DetentionRecord) -> Document:
        doc = Document(document_type="ReleaseAct", created_by=record.id)
        doc.generate(record)
        return doc

    def export_to_excel(self, data: List) -> None:
        pass

    def print_document(self, doc: Document) -> None:
        doc.print()

    def send_alert(self, record: DetentionRecord) -> None:
        self.notification_log.append(f"Alert for record {record.id}")

    def check_deadlines(self) -> None:
        pass

    def schedule_reminder(self, record: DetentionRecord, delay: int) -> None:
        self.notification_log.append(f"Reminder for {record.id} after {delay} min")

    def cancel_reminder(self, reminder_id: uuid.UUID) -> None:
        pass

    def get_active_alerts(self) -> List[str]:
        return self.notification_log
