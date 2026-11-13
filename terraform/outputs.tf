output "worker_role_arn" {
  value = aws_iam_role.worker.arn
}

output "publisher_role_arn" {
  value = aws_iam_role.publisher.arn
}

output "reader_role_arn" {
  value = aws_iam_role.reader.arn
}

output "topic_arn" {
  value = aws_sns_topic.events.arn
}

output "orders_queue_url" {
  value = aws_sqs_queue.orders.id
}

output "audit_queue_url" {
  value = aws_sqs_queue.audit.id
}

output "dlq_url" {
  value = aws_sqs_queue.dlq.id
}
