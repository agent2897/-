"""Python package for Lab 3 UML implementation."""

from .models import (
    Person,
    Detainee,
    Staff,
    DutyOfficer,
    MedicalStaff,
    DetentionRecord,
    Cell,
    CellAssignment,
    Event,
    Document,
    StoredProperty,
    AuditLog,
    NotificationService,
    ReportGenerator,
)
from .repository import Repository

__all__ = [
    "Person",
    "Detainee",
    "Staff",
    "DutyOfficer",
    "MedicalStaff",
    "DetentionRecord",
    "Cell",
    "CellAssignment",
    "Event",
    "Document",
    "StoredProperty",
    "AuditLog",
    "NotificationService",
    "ReportGenerator",
    "Repository",
]
