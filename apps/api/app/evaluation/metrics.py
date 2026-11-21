from math import log2


def metrics(ranked, relevant):
    hits = [int(item in relevant) for item in ranked]
    result = {"mrr": next((1 / i for i, h in enumerate(hits, 1) if h), 0)}
    for k in (5, 10):
        found = sum(hits[:k])
        ideal = sum(1 / log2(i + 2) for i in range(min(k, len(relevant))))
        result.update(
            {
                f"recall_{k}": found / max(1, len(relevant)),
                f"precision_{k}": found / k,
                f"ndcg_{k}": sum(h / log2(i + 2) for i, h in enumerate(hits[:k])) / ideal if ideal else 0,
            }
        )
    return result
