from dataclasses import dataclass


NOTE_CREATED = "note_created"


@dataclass
class NoteCreatedEvent:
    ts_code: str
    note_content: str
