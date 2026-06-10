from typing import TypedDict


class Prompt(TypedDict):
    id: str
    strategy: str
    granularity: str
    text: str


PROMPT_LIBRARY: dict[str, Prompt] = {
    "v1_zero_shot": {
        "id": "v1_zero_shot",
        "strategy": "zero_shot",
        "granularity": "full_doc",
        "text": (
            "Is this document tampered or forged? "
            "Answer with only 'yes' or 'no'."
        ),
    },
    "v1_cot": {
        "id": "v1_cot",
        "strategy": "chain_of_thought",
        "granularity": "full_doc",
        "text": (
            "Examine this document carefully. Walk through each element — "
            "text fields, dates, names, figures, stamps, and layout — "
            "noting any inconsistencies. Then conclude: is this document "
            "tampered or genuine?"
        ),
    },
    "v1_structured": {
        "id": "v1_structured",
        "strategy": "structured_output",
        "granularity": "full_doc",
        "text": (
            "Analyse this document for signs of tampering. "
            "Respond in JSON with this exact structure:\n"
            "{\n"
            '  "tampered": true | false,\n'
            '  "confidence": "low" | "medium" | "high",\n'
            '  "findings": {\n'
            '    "text_fields": "<observation>",\n'
            '    "stamps_seals": "<observation>",\n'
            '    "layout_alignment": "<observation>",\n'
            '    "semantic_coherence": "<observation>"\n'
            "  },\n"
            '  "rationale": "<one sentence summary>"\n'
            "}"
        ),
    },
    "v1_targeted_stamp": {
        "id": "v1_targeted_stamp",
        "strategy": "targeted_probe",
        "granularity": "region_stamp",
        "text": (
            "Focus only on the official stamp or seal in this image. "
            "Assess: placement, color saturation, edge artifacts, and whether "
            "it appears genuine. Is this stamp authentic or manipulated?"
        ),
    },
    "v1_targeted_text": {
        "id": "v1_targeted_text",
        "strategy": "targeted_probe",
        "granularity": "region_text",
        "text": (
            "Focus only on the text fields in this document — names, dates, "
            "salary figures, and other typed content. Do any fields look "
            "inconsistent in font, spacing, or alignment with the rest of "
            "the document?"
        ),
    },
}
