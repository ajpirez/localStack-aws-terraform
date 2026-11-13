#!/usr/bin/env python3
"""Crea roles, Lambdas, SQS y SNS de prueba, y publica los pedidos de messages.json."""

import json
import os
import platform
import subprocess
import tempfile
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
PROJECT = "localstack-demo"

WORKER_ROLE = "demo-lambda-worker"
PUBLISHER_ROLE = "demo-lambda-publisher"
READER_ROLE = "demo-orders-reader"
DLQ_NAME = "demo-orders-dlq"
ORDERS_QUEUE = "demo-orders"
AUDIT_QUEUE = "demo-orders-audit"
TOPIC_NAME = "demo-events"
WORKER_FUNCTION = "demo-worker"
PUBLISHER_FUNCTION = "demo-publisher"

if ROOT == Path("/opt/localstack-seed"):
    AWS = ["awslocal"]
else:
    AWS = [str(ROOT.parent / "scripts" / "awslocal")]

ENV = os.environ.copy()
ENV["AWS_PAGER"] = ""
ENV.setdefault("AWS_DEFAULT_REGION", REGION)


def run(args, check=True, query=None):
    command = [*AWS, *args]
    if query:
        command += ["--query", query, "--output", "text"]
    result = subprocess.run(command, capture_output=True, text=True, env=ENV)
    if check and result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise SystemExit(f"$ {' '.join(command)}\n{detail}")
    return result


def aws(args, query=None):
    command = list(args)
    if query:
        command += ["--query", query]
    if "--query" in command and "--output" not in command:
        command += ["--output", "text"]
    return run(command).stdout.strip()


def exists(args):
    return run(args, check=False).returncode == 0


def render(path, replacements):
    text = path.read_text()
    for key, value in replacements.items():
        text = text.replace(key, value)
    handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    handle.write(text)
    handle.close()
    return handle.name


def ensure_role(name, trust_file):
    if exists(["iam", "get-role", "--role-name", name]):
        aws(
            [
                "iam",
                "update-assume-role-policy",
                "--role-name",
                name,
                "--policy-document",
                f"file://{trust_file}",
            ]
        )
    else:
        aws(
            [
                "iam",
                "create-role",
                "--role-name",
                name,
                "--assume-role-policy-document",
                f"file://{trust_file}",
                "--tags",
                f"Key=Project,Value={PROJECT}",
            ]
        )
    return aws(["iam", "get-role", "--role-name", name, "--query", "Role.Arn"])


def put_policy(role_name, policy_name, document):
    handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    json.dump(document, handle)
    handle.close()
    aws(
        [
            "iam",
            "put-role-policy",
            "--role-name",
            role_name,
            "--policy-name",
            policy_name,
            "--policy-document",
            f"file://{handle.name}",
        ]
    )


def queue_url(name):
    return aws(["sqs", "create-queue", "--queue-name", name, "--query", "QueueUrl"])


def queue_arn(url):
    return aws(
        [
            "sqs",
            "get-queue-attributes",
            "--queue-url",
            url,
            "--attribute-names",
            "QueueArn",
            "--query",
            "Attributes.QueueArn",
        ]
    )


def set_attributes(url, attributes):
    handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    json.dump({key: str(value) for key, value in attributes.items()}, handle)
    handle.close()
    aws(
        [
            "sqs",
            "set-queue-attributes",
            "--queue-url",
            url,
            "--attributes",
            f"file://{handle.name}",
        ]
    )


def allow_sns(queue_arn_value, topic_arn):
    return json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "sns.amazonaws.com"},
                    "Action": "sqs:SendMessage",
                    "Resource": queue_arn_value,
                    "Condition": {"ArnEquals": {"aws:SourceArn": topic_arn}},
                }
            ],
        }
    )


def zip_source(source, target):
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.write(source, source.name)


def lambda_arch():
    return "arm64" if platform.machine() in {"arm64", "aarch64"} else "x86_64"


def ensure_function(name, role_arn, source, environment):
    package = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
    package.close()
    zip_source(source, package.name)
    config = {
        "FunctionName": name,
        "Runtime": "python3.12",
        "Role": role_arn,
        "Handler": f"{source.stem}.handler",
        "Timeout": 15,
        "MemorySize": 256,
        "Architectures": [lambda_arch()],
        "Environment": {"Variables": environment},
        "Tags": {"Project": PROJECT},
    }
    if exists(["lambda", "get-function", "--function-name", name]):
        aws(
            [
                "lambda",
                "update-function-code",
                "--function-name",
                name,
                "--zip-file",
                f"fileb://{package.name}",
            ]
        )
        wait_updated(name)
        aws(
            [
                "lambda",
                "update-function-configuration",
                "--function-name",
                name,
                "--role",
                role_arn,
                "--handler",
                config["Handler"],
                "--timeout",
                str(config["Timeout"]),
                "--memory-size",
                str(config["MemorySize"]),
                "--environment",
                json.dumps(config["Environment"]),
            ]
        )
        wait_updated(name)
    else:
        handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        json.dump(config, handle)
        handle.close()
        aws(
            [
                "lambda",
                "create-function",
                "--cli-input-json",
                f"file://{handle.name}",
                "--zip-file",
                f"fileb://{package.name}",
            ]
        )
        wait_active(name)


def wait_active(name):
    for _ in range(40):
        state = aws(
            ["lambda", "get-function", "--function-name", name, "--query", "Configuration.State"]
        )
        if state == "Active":
            return
        time.sleep(2)
    raise SystemExit(f"{name} no llegó a Active")


def wait_updated(name):
    for _ in range(40):
        state = aws(
            [
                "lambda",
                "get-function",
                "--function-name",
                name,
                "--query",
                "Configuration.LastUpdateStatus",
            ]
        )
        if state == "Successful":
            return
        if state == "Failed":
            raise SystemExit(f"La actualización de {name} falló")
        time.sleep(2)
    raise SystemExit(f"{name} no terminó de actualizarse")


def ensure_mapping(function_name, source_arn):
    current = aws(
        [
            "lambda",
            "list-event-source-mappings",
            "--function-name",
            function_name,
            "--query",
            f"EventSourceMappings[?EventSourceArn=='{source_arn}'].UUID | [0]",
        ]
    )
    if current and current != "None":
        return current
    return aws(
        [
            "lambda",
            "create-event-source-mapping",
            "--function-name",
            function_name,
            "--event-source-arn",
            source_arn,
            "--batch-size",
            "5",
            "--enabled",
            "--query",
            "UUID",
        ]
    )


def ensure_subscription(topic_arn, queue_arn_value):
    current = aws(
        [
            "sns",
            "list-subscriptions-by-topic",
            "--topic-arn",
            topic_arn,
            "--query",
            f"Subscriptions[?Endpoint=='{queue_arn_value}'].SubscriptionArn | [0]",
        ]
    )
    if current and current != "None":
        aws(
            [
                "sns",
                "set-subscription-attributes",
                "--subscription-arn",
                current,
                "--attribute-name",
                "RawMessageDelivery",
                "--attribute-value",
                "true",
            ]
        )
        return current
    return aws(
        [
            "sns",
            "subscribe",
            "--topic-arn",
            topic_arn,
            "--protocol",
            "sqs",
            "--notification-endpoint",
            queue_arn_value,
            "--attributes",
            "RawMessageDelivery=true",
            "--query",
            "SubscriptionArn",
        ]
    )


def publish_messages(topic_arn, messages):
    ids = []
    for message in messages:
        message_id = aws(
            [
                "sns",
                "publish",
                "--topic-arn",
                topic_arn,
                "--subject",
                message["type"],
                "--message",
                json.dumps(message),
                "--message-attributes",
                json.dumps(
                    {
                        "type": {"DataType": "String", "StringValue": message["type"]},
                        "orderId": {"DataType": "String", "StringValue": message["orderId"]},
                    }
                ),
                "--query",
                "MessageId",
            ]
        )
        ids.append(message_id)
    return ids


def message_count(url):
    return aws(
        [
            "sqs",
            "get-queue-attributes",
            "--queue-url",
            url,
            "--attribute-names",
            "ApproximateNumberOfMessages",
            "--query",
            "Attributes.ApproximateNumberOfMessages",
        ]
    )


def main():
    account = aws(["sts", "get-caller-identity", "--query", "Account"])
    replacements = {"__ACCOUNT__": account}
    print(f"Cuenta {account} en {REGION}")

    reader_trust = render(ROOT / "iam" / "reader-trust.json", replacements)
    lambda_trust = ROOT / "iam" / "lambda-trust.json"
    worker_role_arn = ensure_role(WORKER_ROLE, lambda_trust)
    publisher_role_arn = ensure_role(PUBLISHER_ROLE, lambda_trust)
    reader_role_arn = ensure_role(READER_ROLE, reader_trust)

    dlq_url = queue_url(DLQ_NAME)
    orders_url = queue_url(ORDERS_QUEUE)
    audit_url = queue_url(AUDIT_QUEUE)
    dlq_arn = queue_arn(dlq_url)
    orders_arn = queue_arn(orders_url)
    audit_arn = queue_arn(audit_url)
    topic_arn = aws(["sns", "create-topic", "--name", TOPIC_NAME, "--query", "TopicArn"])

    redrive = json.dumps({"deadLetterTargetArn": dlq_arn, "maxReceiveCount": "3"})
    set_attributes(orders_url, {"VisibilityTimeout": "30", "RedrivePolicy": redrive})
    set_attributes(audit_url, {"VisibilityTimeout": "30"})
    set_attributes(orders_url, {"Policy": allow_sns(orders_arn, topic_arn), "VisibilityTimeout": "30", "RedrivePolicy": redrive})
    set_attributes(audit_url, {"Policy": allow_sns(audit_arn, topic_arn), "VisibilityTimeout": "30"})

    put_policy(
        WORKER_ROLE,
        "consume-orders",
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
                    "Resource": f"arn:aws:logs:{REGION}:{account}:*",
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "sqs:ReceiveMessage",
                        "sqs:DeleteMessage",
                        "sqs:GetQueueAttributes",
                        "sqs:ChangeMessageVisibility",
                    ],
                    "Resource": orders_arn,
                },
            ],
        },
    )
    put_policy(
        PUBLISHER_ROLE,
        "publish-events",
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
                    "Resource": f"arn:aws:logs:{REGION}:{account}:*",
                },
                {"Effect": "Allow", "Action": "sns:Publish", "Resource": topic_arn},
            ],
        },
    )
    put_policy(
        READER_ROLE,
        "read-audit",
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": ["sqs:ReceiveMessage", "sqs:GetQueueAttributes", "sqs:GetQueueUrl"],
                    "Resource": audit_arn,
                },
                {
                    "Effect": "Allow",
                    "Action": ["sns:GetTopicAttributes", "sns:ListSubscriptionsByTopic"],
                    "Resource": topic_arn,
                },
            ],
        },
    )

    orders_sub = ensure_subscription(topic_arn, orders_arn)
    audit_sub = ensure_subscription(topic_arn, audit_arn)

    print("Creando Lambdas (la primera vez puede bajar la imagen del runtime)...")
    ensure_function(
        WORKER_FUNCTION,
        worker_role_arn,
        ROOT / "lambda" / "worker.py",
        {"AWS_DEFAULT_REGION": REGION},
    )
    ensure_function(
        PUBLISHER_FUNCTION,
        publisher_role_arn,
        ROOT / "lambda" / "publisher.py",
        {
            "AWS_DEFAULT_REGION": REGION,
            "AWS_ENDPOINT_URL": "http://localhost.localstack.cloud:4566",
            "TOPIC_ARN": topic_arn,
        },
    )
    mapping = ensure_mapping(WORKER_FUNCTION, orders_arn)

    messages = json.loads((ROOT / "messages.json").read_text())
    published = publish_messages(topic_arn, messages)

    invoke_out = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    invoke_out.close()
    invoke = run(
        [
            "lambda",
            "invoke",
            "--cli-binary-format",
            "raw-in-base64-out",
            "--function-name",
            PUBLISHER_FUNCTION,
            "--payload",
            json.dumps(
                {
                    "type": "order.created",
                    "orderId": "ord-lambda-1",
                    "amount": 10,
                    "currency": "USD",
                    "customerId": "cust-lambda",
                }
            ),
            invoke_out.name,
        ],
        check=False,
    )
    invoke_body = Path(invoke_out.name).read_text().strip()
    if invoke.returncode != 0 or "FunctionError" in invoke.stdout:
        raise SystemExit(
            "demo-publisher no pudo publicar.\n"
            f"{invoke.stderr.strip()}\n{invoke.stdout.strip()}\n{invoke_body}"
        )

    time.sleep(2)
    print()
    print("Datos de prueba listos")
    print(f"  rol worker     {worker_role_arn}")
    print(f"  rol publisher  {publisher_role_arn}")
    print(f"  rol reader     {reader_role_arn}")
    print(f"  topic          {topic_arn}")
    print(f"  cola orders    {orders_url}  (la consume demo-worker)")
    print(f"  cola audit     {audit_url}  ({message_count(audit_url)} mensajes visibles)")
    print(f"  cola dlq       {dlq_url}")
    print(f"  suscripción orders  {orders_sub}")
    print(f"  suscripción audit   {audit_sub}")
    print(f"  mapping        {mapping}")
    print(f"  publicados     {len(published)} en SNS, más ord-lambda-1 vía Lambda")
    print(f"  invoke         {invoke_body}")
    print()
    print("Ver la cola que conserva los mensajes:")
    print(f"  ./scripts/awslocal sqs receive-message --queue-url {audit_url} --max-number-of-messages 5 --visibility-timeout 0")
    print("Probar el rol de solo lectura:")
    print(f"  ./scripts/awslocal sts assume-role --role-arn {reader_role_arn} --role-session-name demo")


if __name__ == "__main__":
    main()
