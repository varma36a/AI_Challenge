Tools:

- predict_customer(payload: CustomerFeatures) -> {label, proba}
- get_stat(key: string) -> any

Task types:

- intent="predict": validate payload, call predict_customer, then return 3 bullets.
- intent="eda": fetch 1–3 stats via get_stat, compact explanation.
- intent="report": summarize EDA + model metrics + suggestions.
