data "archive_file" "worker" {
  type        = "zip"
  source_file = "${path.module}/../lambda/worker.py"
  output_path = "${path.module}/build/worker.zip"
}

data "archive_file" "publisher" {
  type        = "zip"
  source_file = "${path.module}/../lambda/publisher.py"
  output_path = "${path.module}/build/publisher.zip"
}

resource "aws_lambda_function" "worker" {
  function_name    = "demo-worker"
  role             = aws_iam_role.worker.arn
  runtime          = "python3.12"
  handler          = "worker.handler"
  filename         = data.archive_file.worker.output_path
  source_code_hash = data.archive_file.worker.output_base64sha256
  architectures    = [var.lambda_architecture]
  timeout          = 15
  memory_size      = 256
  tags             = local.tags

  environment {
    variables = {
      AWS_DEFAULT_REGION = local.region
    }
  }
}

resource "aws_lambda_function" "publisher" {
  function_name    = "demo-publisher"
  role             = aws_iam_role.publisher.arn
  runtime          = "python3.12"
  handler          = "publisher.handler"
  filename         = data.archive_file.publisher.output_path
  source_code_hash = data.archive_file.publisher.output_base64sha256
  architectures    = [var.lambda_architecture]
  timeout          = 15
  memory_size      = 256
  tags             = local.tags

  environment {
    variables = {
      AWS_DEFAULT_REGION = local.region
      AWS_ENDPOINT_URL   = "http://localhost.localstack.cloud:4566"
      TOPIC_ARN          = aws_sns_topic.events.arn
    }
  }
}

resource "aws_lambda_event_source_mapping" "worker" {
  event_source_arn = aws_sqs_queue.orders.arn
  function_name    = aws_lambda_function.worker.arn
  batch_size       = 5
  enabled          = true
}
