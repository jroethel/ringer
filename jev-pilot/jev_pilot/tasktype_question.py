"""The task_type Choice question and its response accessor.

Accessors are pinned in jev-pilot/SDK-CONTRACT.md against typesafe-sdk==0.7.1.
"""

from typesafe_sdk import Choice

VOCAB = [
    "code-feature", "code-fix", "code-review", "docs",
    "site-build", "persona-review", "probe", "research",
]

CRITERIA = {
    "code-feature": "Implementing new functionality, infrastructure, or capability in code.",
    "code-fix": "Repairing a bug, regression, or defect in existing code.",
    "code-review": "Reviewing, auditing, or critiquing code without implementing changes.",
    "docs": "Writing or editing documentation, reference prose, or explanatory text with no code deliverable.",
    "site-build": "Building, styling, or assembling a website, HTML page, or visual or branded deliverable.",
    "persona-review": "Reviewing an artifact for alignment with a persona, voice, or audience fit.",
    "probe": "Running a diagnostic probe, smoke test, or capability check.",
    "research": "Gathering, fetching, or synthesizing external information into findings.",
}

INSTRUCTIONS = "Classify the software task described in `task_spec` into exactly one task type."

_CODE_FAMILY = {"code-feature", "code-fix", "code-review"}


def build_question() -> dict:
    """The single flat Choice over the eight task types."""
    return {"task_type": Choice(instructions=INSTRUCTIONS, criteria=CRITERIA)}


def classify(client, spec: str, model: str = "jev-latest") -> dict:
    """Ask Jev for one task_type and read the pinned accessors off the response."""
    response = client.system_one(
        state={"task_spec": spec},
        questions=build_question(),
        model=model,
    )
    answer = response.choices["task_type"]
    return {
        "choice": answer.choice,
        "probabilities": answer.probabilities,
        "confidence": answer.confidence,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    }


def parent_label(label: str) -> str:
    """Collapse the code family to `code`; every other label is its own parent."""
    return "code" if label in _CODE_FAMILY else label
