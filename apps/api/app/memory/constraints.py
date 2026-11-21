import re
from pydantic import ValidationError
from app.schemas.domain import Constraints


class ConstraintConflict(ValueError):
    pass


CLEAR = re.compile(r"\b(?:clear|reset|remove) (?:all )?(?:search )?filters\b")
CLAUSE = re.compile(r"[,;.!?]|\b(?:but|however|while|instead)\b")
TOKENS = re.compile(
    r"(?P<negate>\b(?:exclude|avoid|without|except|no|not|never|don't|don't want)\b)"
    r"|(?P<include>\b(?:include|only|require|find)\b)"
    r"|(?P<mode>\b(?:remote|on[ -]?site|hybrid)\b)"
    r"|(?P<employment>\b(?:internships?|interns?|full[ -]?time)\b)"
)


def parse_followup(message: str, previous: dict) -> tuple[str, Constraints]:
    lower = message.lower().replace("’", "'")
    patch: dict[str, object] = {}
    positive: dict[str, set[str]] = {}
    negative: dict[str, list[str]] = {}
    for clause in CLAUSE.split(lower):
        excluded = False
        last_exclusion: tuple[str, int] | None = None
        if re.search(r"\b(?:not only|no preference|do not care|don't care)\b", clause) and TOKENS.search(
            clause
        ):
            raise ConstraintConflict(
                "Should work mode and employment type be required, excluded, or left open?"
            )
        for match in TOKENS.finditer(clause):
            if match.lastgroup == "negate":
                excluded = True
                last_exclusion = None
            elif match.lastgroup == "include":
                excluded = False
            else:
                field = match.lastgroup
                assert field is not None
                value = match[0].replace("-", "").replace(" ", "")
                value = "internship" if value.startswith("intern") else value
                value = "full-time" if value == "fulltime" else value
                if excluded:
                    if last_exclusion and last_exclusion[0] != field:
                        between = clause[last_exclusion[1] : match.start()]
                        if not re.search(r"\b(?:and|or)\b", between):
                            raise ConstraintConflict(
                                "Do you want to exclude that combination, or exclude each condition separately?"
                            )
                    negative.setdefault(field, []).append(value)
                    last_exclusion = (field, match.end())
                else:
                    positive.setdefault(field, set()).add(value)
    for field, values in positive.items():
        if len(values) > 1:
            raise ConstraintConflict(f"Choose one required {field.replace('_', ' ')} or clear the filter.")
        patch[field] = next(iter(values))
    if CLEAR.search(lower):
        previous = {}
    for field, exclusions in negative.items():
        key = f"exclude_{field}"
        patch[key] = list(dict.fromkeys([*(previous.get(key) or []), *exclusions]))
    year = re.search(r"\b(20[2-9]\d)\b", lower)
    if year:
        patch["graduation_year"] = int(year[1])
    if any(x in lower for x in ("ai/ml", "ml internship", "ai engineering", "ai internship")):
        patch["domain"] = "AI/ML"
    if "bangalore" in lower:
        patch["location"] = "Bangalore"
    salary = re.search(r"(?:at least|minimum|paying)\s*([\d,]+)\s*(inr|usd|eur)", lower)
    if salary:
        patch.update(min_salary=float(salary[1].replace(",", "")), currency=salary[2].upper())
        patch["period"] = (
            "year" if "yearly" in lower or "per year" in lower else ("month" if "month" in lower else None)
        )
    if "exclude" in lower and ("three years" in lower or "3 years" in lower):
        patch["max_experience"] = 2.99
    try:
        return message, Constraints.model_validate({**previous, **patch})
    except ValidationError as exc:
        raise ConstraintConflict(
            "A requirement conflicts with an exclusion. Clear filters and specify the combination you want."
        ) from exc

