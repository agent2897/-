from datetime import datetime, timedelta
from pathlib import Path
import sys

try:
    from .models import Detainee, DetentionRecord, StoredItem
    from .usecases import RegistrationUseCase, DeadlineControlUseCase, ReleaseUseCase
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from models import Detainee, DetentionRecord, StoredItem
    from usecases import RegistrationUseCase, DeadlineControlUseCase, ReleaseUseCase


def run_demo() -> None:
    detainees = []
    audit = []

    registration = RegistrationUseCase(detainees, audit)
    deadline_control = DeadlineControlUseCase(audit)
    release_flow = ReleaseUseCase(audit)

    new_detainee = Detainee(
        full_name="Іваненко Олег Андрійович",
        birth_date=datetime(1992, 3, 12),
        gender="Чоловіча",
        document_number="BB987654",
        address="м. Львів, вул. Січових Стрільців, 10",
        case_number="D-2001",
    )
    detention = DetentionRecord(protocol_number="P-2026-002", article="124", arrival_time=datetime.now())
    detention.calculate_deadline(48)

    print("Registering detainee...")
    if registration.execute(new_detainee, detention):
        print("Registration succeeded", new_detainee.barcode)
    else:
        print("Duplicate or failed registration")

    print("Deadline status:", deadline_control.check_deadline(detention))
    delayed = detention.deadline + timedelta(hours=1) if detention.deadline else datetime.now()
    if deadline_control.extend_deadline(detention, "Court-002", delayed):
        print("Deadline extended to", detention.deadline)
    else:
        print("Deadline extension failed")

    items = [StoredItem(name="Годинник", returned=True), StoredItem(name="Телефон", returned=True)]
    if release_flow.execute(new_detainee, "ended_term", items, comments="Term expired"):
        print("Release completed")
    else:
        print("Release blocked: missing return or invalid basis")

    print("Audit entries:")
    for entry in audit:
        print(entry.action, entry.details)


if __name__ == "__main__":
    run_demo()
