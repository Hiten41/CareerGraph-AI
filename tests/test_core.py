import pytest
from app.schemas.domain import Constraints
from app.retrieval.eligibility import eligibility
from app.retrieval.fusion import rrf
from app.memory.constraints import parse_followup
from app.ranking.scoring import explain
from app.evaluation.metrics import metrics
from app.services.resume import parse_pdf
from app.agents.tools import dispatch


@pytest.mark.parametrize(
    "salary,currency,period,status",
    [
        (55000, "INR", "month", "eligible"),
        (49000, "INR", "month", "ineligible"),
        (90000, "USD", "year", "uncertain"),
        (None, None, None, "uncertain"),
    ],
)
def test_compensation(salary, currency, period, status):
    assert (
        eligibility(
            dict(status="active", salary=salary, currency=currency, period=period),
            Constraints(min_salary=50000, currency="INR", period="month"),
        )[0]
        == status
    )


def test_expired():
    assert eligibility({"status": "expired"}, Constraints())[0] == "ineligible"


def test_fusion():
    scores = rrf([["a", "b", "b"], ["b", "c"]])
    assert scores["b"] == pytest.approx(1 / 62 + 1 / 61)


def test_followup():
    c = {}
    for m in [
        "Find remote Python internships for 2028 graduates",
        "Only AI/ML ones",
        "At least 50,000 INR per month",
    ]:
        _, parsed = parse_followup(m, c)
        c = parsed.model_dump(exclude_none=True)
    assert c == dict(
        employment="internship",
        mode="remote",
        graduation_year=2028,
        domain="AI/ML",
        min_salary=50000,
        currency="INR",
        period="month",
    )


def test_feedback_and_evidence():
    j = dict(title="Backend", description="Build APIs", skills=["SQL", "Python"])
    base = explain(j, {"skills": ["sql"]}, 0, [])
    assert base["matched"] == ["sql"] and base["missing"] == ["python"]
    assert explain(j, {"skills": ["sql"]}, 0, ["backend"], 1)["score"] > base["score"]


def test_metrics():
    r = metrics(["x", "b", "a"], {"a", "b"})
    assert r["mrr"] == 0.5 and r["precision_5"] == 0.4 and r["recall_5"] == 1 and 0 < r["ndcg_5"] < 1


def test_private_writes():
    with pytest.raises(ValueError):
        dispatch("save_user_preferences", {}, None, None, {"pending_preference": "backend"})


@pytest.mark.parametrize("data", [b"invalid", b"%PDF-malformed"])
def test_pdf_rejection(data):
    with pytest.raises(ValueError):
        parse_pdf(data)


def test_profile_cannot_overturn_clear_topical_gap():
    strong = dict(title="Search", description="Index documents", skills=["Go"])
    weak = dict(title="Backend", description="Build APIs", skills=["SQL"])
    profile = {"skills": ["SQL"]}
    assert (
        explain(strong, profile, 1 / 61, [], similarity=0.8)["score"]
        > explain(weak, profile, 1 / 62, ["backend"], 1, similarity=0.4)["score"]
    )
    assert (
        explain(weak, profile, 1 / 62, ["backend"], 1, similarity=0.8)["score"]
        > explain(strong, profile, 1 / 61, [], similarity=0.8)["score"]
    )


@pytest.mark.parametrize(
    ("message", "field", "excluded"),
    [
        ("Exclude remote positions", "mode", ["remote"]),
        ("I do not want internships", "employment", ["internship"]),
        ("No onsite roles please", "mode", ["onsite"]),
        ("No on-site or remote positions", "mode", ["onsite", "remote"]),
    ],
)
def test_negative_followups(message, field, excluded):
    _, constraints = parse_followup(message, {})
    assert getattr(constraints, field) is None
    assert getattr(constraints, f"exclude_{field}") == excluded


def test_exclusions_and_conflicts():
    from app.memory.constraints import ConstraintConflict

    _, constraints = parse_followup("Remote roles, no internships", {})
    assert constraints.mode == "remote" and constraints.exclude_employment == ["internship"]
    assert (
        eligibility({"status": "active", "mode": "remote", "employment": "internship"}, constraints)[0]
        == "ineligible"
    )
    assert eligibility({"status": "active", "mode": "remote"}, constraints)[0] == "uncertain"
    with pytest.raises(ConstraintConflict):
        parse_followup("No remote roles", {"mode": "remote"})
    with pytest.raises(ConstraintConflict):
        parse_followup("remote or hybrid roles", {})
    _, cleared = parse_followup("clear filters", constraints.model_dump())
    assert cleared.model_dump(exclude_none=True) == {}


@pytest.mark.parametrize(
    "message", ["No remote internships", "No preference for remote", "Not only remote roles"]
)
def test_ambiguous_exclusion_asks_for_clarification(message):
    from app.memory.constraints import ConstraintConflict

    with pytest.raises(ConstraintConflict):
        parse_followup(message, {})
