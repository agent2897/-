from datetime import datetime
from pathlib import Path
import sys

try:
    from .models import (
        Detainee,
        DetentionRecord,
        Cell,
        Document,
        SystemState,
    )
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from models import (
        Detainee,
        DetentionRecord,
        Cell,
        Document,
        SystemState,
    )


def run_demo() -> None:
    system = SystemState()

    detainee = Detainee(
        full_name="Петренко Іван Іванович",
        birth_date=datetime(1995, 6, 15).date(),
        gender="Чоловіча",
        document_number="AA123456",
        address="м. Київ, вул. Хрещатик, 1",
        photo_path="photos/petrenko.jpg",
        case_number="D-1001",
        health_status="Задовільний",
    )

    detention = DetentionRecord(
        protocol_number="PR-2026-001",
        article="125",
        division="Патрульна поліція",
    )
    detention.calculate_deadline(24)

    result = system.register_detainee(detainee, detention)
    print("Registration result:", result)
    print("Barcode:", detainee.barcode)
    print("Deadline indicator:", detention.deadline_indicator())

    cell = Cell(id=1, number="A-1", capacity=2, gender_type="Чоловіча", is_medical=False)
    system.cells.append(cell)
    if cell.assign():
        detention.cell_id = cell.id
        print("Assigned to cell", cell.number)

    document = Document(document_type="RegistrationCard")
    document.generate_pdf()
    system.documents.append(document)
    print("Generated document path:", document.file_path)

    print("Current cell occupancy:", cell.occupancy)


if __name__ == "__main__":
    run_demo()
