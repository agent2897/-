from datetime import date

from .models import (
    Detainee,
    DutyOfficer,
    MedicalStaff,
    DetentionRecord,
    Cell,
    CellAssignment,
    Event,
    ReportGenerator,
)
from .repository import Repository


def run_demo() -> None:
    detainee = Detainee(
        last_name="Ivanov",
        first_name="Ivan",
        middle_name="Petrovich",
        birth_date=date(1990, 5, 20),
        gender="Male",
        document_number="AB123456",
        address="Kyiv",
        case_number="D-2026-001",
    )

    record = DetentionRecord(protocol_number="P-001", article="125")
    record.calculate_deadline(48)
    detainee.register(record)

    officer = DutyOfficer(
        last_name="Shevchenko",
        first_name="Oksana",
        username="oshev",
        password_hash="pass123",
        role="DutyOfficer",
    )
    officer.start_shift()
    officer.register_detainee(detainee, record)

    medical = MedicalStaff(
        last_name="Kovalenko",
        first_name="Anna",
        username="akov",
        password_hash="med321",
        role="MedicalStaff",
        license_number="MD-9876",
        specialization="General Medicine",
    )
    event = medical.conduct_examination(detainee)
    event.register(record)

    cell = Cell(id=1, cell_number="A1", capacity=4, gender_type="Male", is_medical=False)
    assignment = CellAssignment(detention_id=record.id)
    assignment.assign(cell, record)

    report_generator = ReportGenerator()
    card = report_generator.generate_detainee_card(detainee)
    release_act = report_generator.generate_release_act(record)

    repository = Repository[DetentionRecord](table_name="detention_records")
    repository.save(record)

    print("Detainee:", detainee.get_full_name())
    print("Age:", detainee.get_age())
    print("Current detention status:", detainee.get_current_detention().status)
    print("Cell occupancy:", cell.get_occupancy_rate())
    print("Generated documents:", card.document_type, release_act.document_type)
    print("Repository count:", len(repository.find_all()))


if __name__ == "__main__":
    run_demo()
