from router.models import TASK_KEYWORDS, TASK_ROUTING


def classify(prompt: str, task_type: str | None = None) -> str:
    if task_type and task_type in TASK_ROUTING:
        return task_type
    lower = prompt.lower()
    scores = {}
    for task, keywords in TASK_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in lower)
        if score > 0:
            scores[task] = score
    if not scores:
        return "general"
    return max(scores, key=scores.get)
