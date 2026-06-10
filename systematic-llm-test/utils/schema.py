from dataclasses import dataclass, field
from typing import Literal


DocType = Literal["payslip", "employment_cert", "standalone_stamp"]
TamperType = Literal["text_replacement", "stamp_overlay", "deletion", "cross_tamper", "none"]
Severity = Literal["low", "high", "none"]
AugmentType = Literal["rotate", "brightness", "noise", "blur", "tilt", "none"]
ImageQuality = Literal["digital", "scan_high", "scan_low"]
Split = Literal["dev", "test"]


@dataclass
class ImageRecord:
    image_id: str
    image_path: str
    doc_type: DocType
    is_tampered: bool
    tamper_types: list[TamperType]
    severity: Severity
    is_augmented: bool
    augment_types: list[AugmentType]
    image_quality: ImageQuality
    source_image_id: str | None = None
    split: Split = "dev"


@dataclass
class EvalResult:
    image_id: str
    doc_type: DocType
    is_tampered: bool
    tamper_types: list[TamperType]
    severity: Severity
    image_quality: ImageQuality
    model: str
    prompt_id: str
    iteration: int
    predicted_tampered: bool | None
    predicted_tamper_types: list[str] = field(default_factory=list)
    rationale: str = ""
    raw_response: str = ""
    latency_s: float = 0.0
    error: str = ""
