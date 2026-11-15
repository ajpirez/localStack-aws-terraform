provider "aws" {
  region     = "us-east-1"
  access_key = "test"
  secret_key = "test"

  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {
    iam    = "http://localhost:4566"
    lambda = "http://localhost:4566"
    logs   = "http://localhost:4566"
    sns    = "http://localhost:4566"
    sqs    = "http://localhost:4566"
    sts    = "http://localhost:4566"
  }
}

data "aws_caller_identity" "current" {}

variable "lambda_architecture" {
  type        = string
  default     = "arm64"
  description = "CPU de las Lambdas. arm64 en esta Mac. El runner de GitHub usa x86_64."
}

locals {
  region = "us-east-1"
  tags   = { Project = "localstack-demo" }
}
