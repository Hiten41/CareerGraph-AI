from app.schemas.domain import Constraints


def eligibility(job: dict, constraints: Constraints) -> tuple[str, list[str]]:
    unknown, failed = [], []
    for field in ("employment", "mode", "location", "graduation_year", "domain"):
        wanted = getattr(constraints, field)
        if wanted is None:
            continue
        actual = job.get(field)
        if actual is None:
            unknown.append(field)
        elif str(actual).casefold() != str(wanted).casefold():
            failed.append(field)
    for field in ("mode", "employment"):
        excluded = getattr(constraints, f"exclude_{field}")
        if not excluded:
            continue
        actual = job.get(field)
        if actual is None:
            if field not in unknown:
                unknown.append(field)
        elif actual.casefold() in excluded:
            failed.append(f"excluded {field}")
    if constraints.max_experience is not None:
        if job.get("experience") is None:
            unknown.append("experience")
        elif job["experience"] > constraints.max_experience:
            failed.append("experience")
    if constraints.min_salary is not None:
        if (
            job.get("salary") is None
            or not constraints.currency
            or not constraints.period
            or job.get("currency") != constraints.currency
            or job.get("period") != constraints.period
        ):
            unknown.append("salary comparison")
        elif job["salary"] < constraints.min_salary:
            failed.append("salary")
    if job.get("status") in ("expired", "archived"):
        failed.append("status")
    elif job.get("status") != "active":
        unknown.append("status")
    return ("ineligible", failed) if failed else (("uncertain", unknown) if unknown else ("eligible", []))
