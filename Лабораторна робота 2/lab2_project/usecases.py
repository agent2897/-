from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys
from typing import List

try:
    from .models import (
        Actor,
        AuditEntry,
        DetentionRecord,
        Detainee,
        Document,
        StoredItem,
    )
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from models import (
        Actor,
        AuditEntry,
        DetentionRecord,
        Detainee,
        Document,
        StoredItem,
    )


class RegistrationUseCase:
    def __init__(self, detainees: List[Detainee], audit: List[AuditEntry]):
        self.detainees = detainees
        self.audit = audit

    def execute(self, detainee: Detainee, detention: DetentionRecord) -> bool:
        if self.find_duplicate(detainee):
            return False
        detainee.generate_barcode()
        detainee.detention = detention
        detainee.status = "active"
        self.detainees.append(detainee)
        self.audit.append(AuditEntry(action="registration", user="system", details=detainee.full_name))
        return True

    def find_duplicate(self, candidate: Detainee) -> bool:
        return any(existing.full_name == candidate.full_name and existing.birth_date == candidate.birth_date for existing in self.detainees)


class DeadlineControlUseCase:
    def __init__(self, audit: List[AuditEntry]):
        self.audit = audit

    def check_deadline(self, detention: DetentionRecord) -> str:
        indicator = detention.indicator()
        if indicator == "red":
            self.audit.append(AuditEntry(action="deadline_alert", user="system", details=f"expired {detention.id}"))
        return indicator

    def extend_deadline(self, detention: DetentionRecord, decision_number: str, new_deadline: datetime) -> bool:
        if detention.extend(decision_number, new_deadline):
            self.audit.append(AuditEntry(action="deadline_extended", user="system", details=decision_number))
            return True
        return False


class ReleaseUseCase:
    def __init__(self, audit: List[AuditEntry]):
        self.audit = audit

    def execute(self, detainee: Detainee, basis: str, items: List[StoredItem], comments: str = "") -> bool:
        if any(not item.returned for item in items):
            return False
        if basis == "court_decision" and not comments:
            return False
        detainee.status = "released"
        if detainee.detention:
            detainee.detention.status = "released"
        document = Document(document_type="ReleaseAct")
        document.save_pdf()
        self.audit.append(AuditEntry(action="release", user="system", details=basis))
        return True
