locals {
  messages = jsondecode(file("${path.module}/messages.json"))
}

resource "terraform_data" "seed_messages" {
  triggers_replace = [filemd5("${path.module}/messages.json")]

  depends_on = [
    aws_sns_topic_subscription.orders,
    aws_sns_topic_subscription.audit,
    aws_lambda_event_source_mapping.worker,
  ]

  provisioner "local-exec" {
    interpreter = ["python3", "-c"]
    command     = <<-PY
import json, os, subprocess
messages = json.loads(r'''${jsonencode(local.messages)}''')
topic = "${aws_sns_topic.events.arn}"
awslocal = "${path.module}/../scripts/awslocal"
for message in messages:
    subprocess.run([
        awslocal, "sns", "publish",
        "--topic-arn", topic,
        "--subject", message["type"],
        "--message", json.dumps(message),
        "--message-attributes", json.dumps({
            "type": {"DataType": "String", "StringValue": message["type"]},
            "orderId": {"DataType": "String", "StringValue": message["orderId"]},
        }),
    ], check=True)
PY
  }
}

resource "aws_lambda_invocation" "publisher_demo" {
  function_name = aws_lambda_function.publisher.function_name
  input = jsonencode({
    type       = "order.created"
    orderId    = "ord-lambda-1"
    amount     = 10
    currency   = "USD"
    customerId = "cust-lambda"
  })

  depends_on = [
    aws_sns_topic_subscription.orders,
    aws_sns_topic_subscription.audit,
    aws_iam_role_policy.publisher,
  ]
}
