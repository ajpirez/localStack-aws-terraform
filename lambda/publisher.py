import json
import os

import boto3


def endpoint_url():
    configured = os.environ.get("AWS_ENDPOINT_URL")
    if configured:
        return configured
    host = os.environ.get("LOCALSTACK_HOSTNAME", "localhost.localstack.cloud")
    return f"http://{host}:4566"


def handler(event, context):
    message = {
        "type": event.get("type", "order.created"),
        "orderId": event.get("orderId", "ord-lambda"),
        "amount": event.get("amount", 0),
        "currency": event.get("currency", "USD"),
        "customerId": event.get("customerId", "cust-lambda"),
        "source": "demo-publisher",
    }
    response = boto3.client("sns", endpoint_url=endpoint_url()).publish(
        TopicArn=os.environ["TOPIC_ARN"],
        Message=json.dumps(message),
        Subject=message["type"],
        MessageAttributes={
            "type": {"DataType": "String", "StringValue": message["type"]},
            "orderId": {"DataType": "String", "StringValue": message["orderId"]},
        },
    )
    print(json.dumps({"published": message, "messageId": response["MessageId"]}))
    return {"messageId": response["MessageId"], "order": message}
