resource "aws_sns_topic" "events" {
  name = "demo-events"
  tags = local.tags
}

resource "aws_sns_topic_subscription" "orders" {
  topic_arn            = aws_sns_topic.events.arn
  protocol             = "sqs"
  endpoint             = aws_sqs_queue.orders.arn
  raw_message_delivery = true

  depends_on = [aws_sqs_queue_policy.orders]
}

resource "aws_sns_topic_subscription" "audit" {
  topic_arn            = aws_sns_topic.events.arn
  protocol             = "sqs"
  endpoint             = aws_sqs_queue.audit.arn
  raw_message_delivery = true

  depends_on = [aws_sqs_queue_policy.audit]
}
