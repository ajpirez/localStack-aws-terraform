resource "aws_sqs_queue" "dlq" {
  name = "demo-orders-dlq"
  tags = local.tags
}

resource "aws_sqs_queue" "orders" {
  name                       = "demo-orders"
  visibility_timeout_seconds = 30
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3
  })
  tags = local.tags
}

resource "aws_sqs_queue" "audit" {
  name                       = "demo-orders-audit"
  visibility_timeout_seconds = 30
  tags                       = local.tags
}

data "aws_iam_policy_document" "orders_queue" {
  statement {
    effect    = "Allow"
    actions   = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.orders.arn]

    principals {
      type        = "Service"
      identifiers = ["sns.amazonaws.com"]
    }

    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"
      values   = [aws_sns_topic.events.arn]
    }
  }
}

data "aws_iam_policy_document" "audit_queue" {
  statement {
    effect    = "Allow"
    actions   = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.audit.arn]

    principals {
      type        = "Service"
      identifiers = ["sns.amazonaws.com"]
    }

    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"
      values   = [aws_sns_topic.events.arn]
    }
  }
}

resource "aws_sqs_queue_policy" "orders" {
  queue_url = aws_sqs_queue.orders.id
  policy    = data.aws_iam_policy_document.orders_queue.json
}

resource "aws_sqs_queue_policy" "audit" {
  queue_url = aws_sqs_queue.audit.id
  policy    = data.aws_iam_policy_document.audit_queue.json
}
