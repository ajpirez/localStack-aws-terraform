import json


def handler(event, context):
    records = event.get("Records") or []
    if not records:
        print(json.dumps({"mode": "direct", "event": event}))
        return {"processed": 0}

    orders = []
    for record in records:
        body = record.get("body", "")
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = {"raw": body}
        item = {
            "messageId": record.get("messageId"),
            "orderId": payload.get("orderId"),
            "type": payload.get("type"),
            "amount": payload.get("amount"),
        }
        print(json.dumps(item))
        orders.append(item)
    return {"processed": len(orders), "orders": orders}
