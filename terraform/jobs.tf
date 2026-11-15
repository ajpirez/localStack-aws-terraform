resource "aws_sqs_queue" "jobs_dlq" {
  name = "demo-jobs-dlq"
  tags = local.tags
}

resource "aws_sqs_queue" "jobs" {
  name                       = "demo-jobs"
  visibility_timeout_seconds = 30
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.jobs_dlq.arn
    maxReceiveCount     = 3
  })
  tags = local.tags
}

resource "aws_iam_policy" "jobs_publisher" {
  name = "demo-jobs-publisher"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["sqs:SendMessage", "sqs:GetQueueUrl"]
        Resource = aws_sqs_queue.jobs.arn
      },
    ]
  })
}

resource "aws_iam_policy" "jobs_worker" {
  name = "demo-jobs-worker"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
          "sqs:ChangeMessageVisibility",
        ]
        Resource = [aws_sqs_queue.jobs.arn, aws_sqs_queue.jobs_dlq.arn]
      },
    ]
  })
}

output "jobs_queue_url" {
  value = aws_sqs_queue.jobs.id
}

output "jobs_dlq_url" {
  value = aws_sqs_queue.jobs_dlq.id
}
