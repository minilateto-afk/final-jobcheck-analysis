from config import CATEGORY_RULES


def classify_violation(row):
    text = f"{row.get('violated_law', '')} {row.get('violation_content', '')}"

    for category, keywords in CATEGORY_RULES.items():
        for keyword in keywords:
            if keyword in text:
                return category

    return "其他"