import os, json, httpx
from typing import Any, Dict, Optional, Tuple
from .schemas import CustomerFeatures

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "stats.json")

def get_stat(key: str):
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        stats = json.load(f)
    return stats.get(key)

def _normalize_response(obj: Any) -> Any:
    """
    Try to coerce common AML responses to a friendly shape.
    Otherwise return the original object.
    """
    try:
        # e.g. {"predictions":[{"label":"Satisfied","probabilities":{"Satisfied":0.81,"Dissatisfied":0.19}}]}
        if isinstance(obj, dict) and "predictions" in obj:
            p = obj["predictions"][0]
            if isinstance(p, dict):
                if "label" in p and "probabilities" in p and isinstance(p["probabilities"], dict):
                    label = p["label"]
                    proba = p["probabilities"].get(label)
                    return {"label": label, "proba": proba, "raw": obj}
        # e.g. {"result":[0]} or [0.81] or {"label":"Satisfied","proba":0.81}
        if isinstance(obj, dict) and "label" in obj and "proba" in obj:
            return obj
        if isinstance(obj, dict) and "result" in obj:
            return {"result": obj["result"], "raw": obj}
        if isinstance(obj, list):
            return {"result": obj}
    except Exception:
        pass
    return obj  # unknown format

def predict_customer(payload: Dict[str, Any]):
    # Validate inputs early (raises 422 via FastAPI if bad)
    features = CustomerFeatures(**payload)

    AML_SCORING_URI = os.getenv("AML_SCORING_URI", "").strip()
    AML_API_KEY = os.getenv("AML_API_KEY", "").strip()
    AML_DEPLOYMENT = os.getenv("AML_DEPLOYMENT", "").strip()  # optional

    # Local mock if no endpoint configured
    if not AML_SCORING_URI:
        total_delay = float(features.DepDelay) + float(features.ArrDelay)
        score = 0.5 + (features.SeatComfort - 3) * 0.08 + (features.Cleanliness - 3) * 0.06
        score += (4 - min(total_delay / 60, 4)) * 0.05  # cap effect
        score = max(0.0, min(1.0, score))
        label = "Satisfied" if score >= 0.5 else "Dissatisfied"
        return {
            "label": label,
            "proba": round(score if label == "Satisfied" else 1 - score, 4),
            "source": "mock",
        }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {AML_API_KEY}",
    }
    if AML_DEPLOYMENT:
        headers["azureml-model-deployment"] = AML_DEPLOYMENT

    # Build canonical MLflow/AutoML body first (most likely to work)
    columns = list(payload.keys())
    values = [payload[k] for k in columns]

    candidate_payloads = [
        {"input_data": {"columns": columns, "data": [values]}},  # MLflow/AutoML
        {"input_data": [payload]},                               # Custom handler (list of rows)
        payload,                                                 # Raw dict
    ]

    last_error = None
    with httpx.Client(timeout=30.0) as client:
        for body in candidate_payloads:
            try:
                r = client.post(AML_SCORING_URI, headers=headers, json=body)
                req_id = r.headers.get("x-ms-request-id") or r.headers.get("x-request-id")
                if r.status_code // 100 != 2:
                    last_error = {
                        "status": r.status_code,
                        "request_id": req_id,
                        "tried_body": body,
                        "body_snippet": (r.text or "")[:2000],
                    }
                    continue

                # 2xx with empty content
                if not r.text or not r.text.strip():
                    last_error = {
                        "status": r.status_code,
                        "request_id": req_id,
                        "tried_body": body,
                        "body_snippet": "",
                        "note": "Empty 2xx response",
                    }
                    continue

                try:
                    obj = r.json()
                except Exception:
                    return {
                        "status": r.status_code,
                        "request_id": req_id,
                        "text": (r.text or "")[:2000],
                        "tried_body": body,
                    }

                return _normalize_response(obj)

            except Exception as ex:
                last_error = {"exception": str(ex), "tried_body": body}

    # All attempts failed — surface diagnostics
    return {
        "error": "AML endpoint call failed",
        "hint": "Match the request body to the 'Consume' tab exactly and verify key/headers.",
        "details": last_error,
    }
