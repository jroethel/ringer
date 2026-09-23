# TypeSafe SDK contract (pinned)

This file pins the facts the pilot code depends on, so the response-accessor logic is settled before any code and before any live call.
Every quote below is verbatim from the page named above it.
All three pages were fetched live on 2026-09-22 and all three returned HTTP 200.

## Pinned version and install command

| Fact             | Value          | Source                                                    |
| ---------------- | -------------- | --------------------------------------------------------- |
| pip package name | `typesafe-sdk` | https://docs.typesafe.ai/sdk/python.md                    |
| pinned version   | `0.7.1`        | PyPI release metadata for `typesafe-sdk`, read 2026-09-22 |
| requires-python  | `>=3.10`       | PyPI release metadata for `typesafe-sdk`, read 2026-09-22 |
| venv python      | 3.12.3         | `jev-pilot/.venv`                                         |

The docs page gives the install command without a version, so the exact version to pin was taken from the PyPI release metadata for that same package name.

Verbatim from https://docs.typesafe.ai/sdk/python.md:

```sh
pip install typesafe-sdk
```

The exact command run inside `jev-pilot/.venv` for this pilot:

```bash
cd /home/jjrdar/repos/ringer && source jev-pilot/.venv/bin/activate && pip install "typesafe-sdk==0.7.1"
```

It reported `Successfully installed ... typesafe-sdk-0.7.1`, and `typesafe_sdk.__version__` reads `0.7.1` in that venv.

## Endpoint and auth

Verbatim from https://docs.typesafe.ai/api.md:

```http
POST https://api.typesafe.ai/v1/systemone
Authorization: Bearer <API_KEY>
Content-Type: application/json
```

Verbatim from https://docs.typesafe.ai/sdk/python.md:

> 2. Set `TYPESAFE_API_KEY` in your environment (create it [here](https://console.typesafe.ai/))

The key is read from the environment only and never appears in code, config, or output.

## Client constructor

Gap, and it is recorded rather than filled from memory: none of the three pages named in the plan's Step 1 carries the client constructor signature.
https://docs.typesafe.ai/sdk/python.md links it as `/sdk/python/api/clients/sync` and `/sdk/python/api/clients/async` but does not reproduce it, and that page was outside the three URLs this step was scoped to fetch.

What the Python SDK page does show, verbatim, is the construction pattern:

```python
from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

with TypeSafeClient() as client:
    response = client.system_one(
        state={"document": "I was charged twice. Please fix this ASAP."},
        questions={
            "billing": Noul(instructions="Is this ticket about billing?"),
            "tone": Choice(
                instructions="What is the customer's tone?",
                criteria={"calm": None, "frustrated": None, "angry": None},
            ),
            "urgency": Score(
                instructions="How urgent is this ticket?",
                criteria=["can wait", "this week", "today"],
            ),
        },
    )

print(response.nouls["billing"].noul)
print(response.choices["tone"].choice)
print(response.scores["urgency"].score)
```

The signature below was read by introspection from the installed `typesafe-sdk==0.7.1`, not from the docs, and is labeled as such:

```python
TypeSafeClient.__init__(
    self, *, api_key: str | None = None, model: str | None = None,
    retry: RetryPolicy | None = None, timeout: float | httpx2.Timeout | None = None,
    headers: Mapping[str, str] | None = None, transport: httpx2.BaseTransport | None = None,
    http_client: httpx2.Client | None = None, base_url: str | None = None,
) -> None
```

Its docstring, verbatim from the installed package, states how the key is read:

> api_key: Required API key; may be set via the `TYPESAFE_API_KEY` environment variable.
> Leading and trailing whitespace is stripped. Empty keys, internal whitespace,
> control characters, and non-ASCII characters are rejected.

So `TypeSafeClient()` with no arguments reads `TYPESAFE_API_KEY` from the environment, which is what the pilot uses.

## system_one signature

Read by introspection from the installed `typesafe-sdk==0.7.1`, labeled as such because the three fetched pages do not carry it:

```python
TypeSafeClient.system_one(
    self, state: JSONContent, questions: Mapping[str, Noul | Choice | Score | NoulModel | ChoiceModel | ScoreModel],
    *, model: str | None = None, retry: RetryPolicy | None = None,
    timeout: float | httpx2.Timeout | None = None,
    extra_headers: Mapping[str, str] | None = None,
    extra_body: Mapping[str, JSONValue | None] | None = None,
    response_model: type[ResponseT] | None = None,
) -> SystemOneResponse | ResponseT
```

`model` is keyword-only, so the pilot passes it by keyword.

Verbatim from https://docs.typesafe.ai/api.md on the `model` field:

> The model that handles the request. Use `"jev-latest"`, TypeSafe's flagship model. See [Models](/models) for the available models and aliases.

## Choice question helper

The SDK exports a `Choice` class, not a lowercase `choice` function, and its arguments are keyword-only.
Read by introspection from the installed `typesafe-sdk==0.7.1`:

```python
Choice(*, type: Literal['choice'] = 'choice', instructions: JSONContent | None = None, criteria: Mapping[str, JSONContent | None])
```

Verbatim from https://docs.typesafe.ai/api.md on a Choice question's `criteria`:

> A map of option to rubric description; use null when an option needs no extra detail. You can have a maximum of 255 options per Choice.

The pilot's eight options are well inside that limit, and every option carries a one-line rubric string rather than null.

## Response accessor (the pinned one)

This is the fact the whole task existed to settle.
Both accessor routes exist: `response.answers[...]` holds every answer keyed by question name, and `response.choices[...]` is a filtered view of the Choice answers.
The pilot pins `response.choices["task_type"]`, because it is the typed, Choice-only accessor shown in the quickstart.

Verbatim from https://docs.typesafe.ai/sdk/python/api/types/responses.md:

> ### typesafe_sdk.SystemOneResponse.choices
> `cached` `property`
> `choices: dict[str, ChoiceAnswer]`
> Choice answers keyed by question name.

> ### typesafe_sdk.SystemOneResponse.answers
> `answers: dict[str, Answer]`
> All answer objects keyed by question name.

> ### typesafe_sdk.SystemOneResponse.usage
> `usage: Usage`
> Token usage for the request.

On `ChoiceAnswer`, verbatim from the same page:

> ### typesafe_sdk.ChoiceAnswer.choice
> `choice: str`
> The name of the choice with the highest probability among the question's criteria.

> ### typesafe_sdk.ChoiceAnswer.confidence
> `confidence: float`
> Confidence in the selected choice, from 0 to 1. Higher values indicate greater certainty; use lower values to flag uncertain selections for review.

> ### typesafe_sdk.ChoiceAnswer.probabilities
> `probabilities: dict[str, float]`
> Probability of each choice in criteria, keyed by choice name, from 0 to 1. Shows how likely the alternatives are; values sum to approximately 1.

On `Usage`, verbatim from the same page:

> ### typesafe_sdk.Usage.input_tokens
> `input_tokens: int | None = None`
> Number of input tokens used, or `None` when the API did not report it.

> ### typesafe_sdk.Usage.output_tokens
> `output_tokens: int | None = None`
> Number of output tokens used, or `None` when the API did not report it.

The pinned accessor table:

| Value                    | Accessor                                      |
| ------------------------ | --------------------------------------------- |
| chosen option            | `response.choices["task_type"].choice`        |
| probability distribution | `response.choices["task_type"].probabilities` |
| confidence               | `response.choices["task_type"].confidence`    |
| input tokens             | `response.usage.input_tokens`                 |
| output tokens            | `response.usage.output_tokens`                |

Token counts are passed through as `int | None` rather than coerced, because the SDK types them that way.

## Justification for the test's FakeResponse shape

The plan's Step 2 licensed reshaping `FakeResponse`, `FakeChoiceAnswer`, and `FakeUsage` to match the pinned accessor.
No reshaping was needed and none was made: the test was transcribed byte-for-byte.
The plan's fake exposes `choices = {"task_type": FakeChoiceAnswer()}` with `.choice`, `.confidence`, and `.probabilities`, plus `usage = FakeUsage()` with `.input_tokens` and `.output_tokens`, which is exactly the shape the verbatim quotes above pin.

## Gaps and unverified items

- The client constructor and the `system_one` signature are not on any of the three fetched pages; they are recorded above from introspection of the installed package and are labeled as such, not quoted from docs.
- `https://docs.typesafe.ai/models` was not fetched in this task, so the per-million token prices are unverified here and stay HC1's job to confirm at run time.
- No live call to `api.typesafe.ai` was made in this task, so the response shape above is pinned from documentation and package types, not from an observed response.
- The plan's `How to run` block lives in the plan file in the jev-research repo, which is outside this task's file ownership, so the version pin is recorded here rather than written back into that block.
