from typing import Any, Dict, List


def normalize_price_payload(prices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized = []
    for item in prices:
        if not isinstance(item, dict):
            continue
        normalized.append({
            "date": item.get("date") or item.get("price_date") or item.get("created_at"),
            "open": item.get("open"),
            "high": item.get("high"),
            "low": item.get("low"),
            "close": item.get("close"),
            "volume": item.get("volume"),
        })
    return normalized


def normalize_prediction_payload(predictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized = []
    for item in predictions:
        if not isinstance(item, dict):
            continue
        normalized.append({
            "date": item.get("date") or item.get("prediction_date"),
            "predicted_close": item.get("predicted_close"),
            "confidence": item.get("confidence"),
        })
    return normalized
