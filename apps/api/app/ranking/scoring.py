def explain(
    job: dict,
    profile: dict,
    retrieval: float,
    preferences: list[str],
    feedback: int = 0,
    *,
    similarity: float = 0,
):
    candidate = {s.casefold() for s in profile.get("skills", [])}
    required = {s.casefold() for s in job["skills"]}
    optional = {s.casefold() for s in job.get("optional_skills", [])}
    matched = sorted(candidate & required)
    overlap = len(matched) / max(1, len(required))
    content = (job["title"] + " " + job["description"]).casefold()
    preference = sum(p.casefold() in content for p in preferences) / max(1, len(preferences))
    features = {
        "retrieval": min(1, retrieval * 30.5),
        "semantic_similarity": max(0.0, min(1.0, similarity)),
        "skill_overlap": overlap,
        "preference": preference,
        "feedback": float(feedback),
    }
    # RRF preserves order but discards the magnitude of a semantic match.
    # Restore that evidence and bound the total effect of personalization.
    topical = 0.5 * features["retrieval"] + 0.5 * features["semantic_similarity"]
    adjustment = 0.02 * overlap + 0.015 * preference + 0.015 * feedback
    features.update(topical=topical, personal_adjustment=adjustment)
    score = topical + adjustment
    return {
        "score": score,
        "features": features,
        "matched": matched,
        "missing": sorted(required - candidate),
        "missing_optional": sorted(optional - candidate),
        "evidence": {"candidate_skills": sorted(candidate), "job_skills": sorted(required)},
        "score_label": "Weighted relevance, not hiring probability",
    }
