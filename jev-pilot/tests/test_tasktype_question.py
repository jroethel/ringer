# jev-pilot/tests/test_tasktype_question.py
from jev_pilot import tasktype_question as q


def test_vocab_is_the_eight_types():
    assert q.VOCAB == [
        "code-feature", "code-fix", "code-review", "docs",
        "site-build", "persona-review", "probe", "research",
    ]


def test_criteria_cover_vocab_with_nonempty_descriptions():
    assert set(q.CRITERIA) == set(q.VOCAB)
    assert all(isinstance(v, str) and v.strip() for v in q.CRITERIA.values())


def test_build_question_shape():
    assert set(q.build_question()) == {"task_type"}


def test_parent_label_maps_code_family_to_code():
    assert q.parent_label("code-feature") == "code"
    assert q.parent_label("code-fix") == "code"
    assert q.parent_label("code-review") == "code"
    assert q.parent_label("docs") == "docs"
    assert q.parent_label("probe") == "probe"


def test_classify_reads_the_pinned_accessor():
    # FakeResponse mirrors the object shape recorded in SDK-CONTRACT.md.
    # Update its construction to match the pinned accessor before running.
    class FakeChoiceAnswer:
        choice = "code-fix"
        confidence = 0.83
        probabilities = {"code-fix": 0.83, "code-feature": 0.17}

    class FakeUsage:
        input_tokens = 300
        output_tokens = 12

    class FakeResponse:
        choices = {"task_type": FakeChoiceAnswer()}
        usage = FakeUsage()

    class FakeClient:
        def system_one(self, state, questions, model):
            assert "task_spec" in state
            return FakeResponse()

    out = q.classify(FakeClient(), spec="fix the crash in the parser")
    assert out == {
        "choice": "code-fix",
        "probabilities": {"code-fix": 0.83, "code-feature": 0.17},
        "confidence": 0.83,
        "input_tokens": 300,
        "output_tokens": 12,
    }
