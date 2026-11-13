# LocalStack + Terraform

AWS local para probar IAM, Lambda, SQS y SNS. LocalStack es el servidor que imita AWS. Terraform es la receta que crea los recursos dentro de ese servidor.

Al terminar tienes un circuito de pedidos:

```mermaid
flowchart LR
  pedidos["messages.json"] --> topic["SNS demo-events"]
  topic --> orders["SQS demo-orders"]
  topic --> audit["SQS demo-orders-audit"]
  orders --> worker["Lambda demo-worker"]
  publisher["Lambda demo-publisher"] --> topic
```

1. `terraform/messages.`
   ```tf
   resource "aws_lambda_function" "publisher" {
     function_name    = "demo-publisher"
     role             = aws_iam_role.publisher.arn
     runtime          = "python3.12"
     handler          = "publisher.handler"
     filename         = data.archive_file.publisher.output_path
     source_code_hash = data.archive_file.publisher.output_base64sha256
     architectures    = ["arm64"]
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
   }resource "aws_lambda_function" "publisher" {
     function_name    = "demo-publisher"
     role             = aws_iam_role.publisher.arn
     runtime          = "python3.12"
     handler          = "publisher.handler"
     filename         = data.archive_file.publisher.output_path
     source_code_hash = data.archive_file.publisher.output_base64sha256
     architectures    = ["arm64"]
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
   }resource "aws_lambda_function" "publisher" {
     function_name    = "demo-publisher"
     role             = aws_iam_role.publisher.arn
     runtime          = "python3.12"
     handler          = "publisher.handler"
     filename         = data.archive_file.publisher.output_path
     source_code_hash = data.archive_file.publisher.output_base64sha256
     architectures    = ["arm64"]
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
   ```

   `json` tiene cuatro pedidos: `ord-1001`, `ord-1002` creado, `ord-1002` pagado y `ord-1003` cancelado.
2. Terraform los publica en el topic **demo-events**. Un topic avisa a todas las colas suscritas.
3. **demo-orders** recibe el pedido y despierta a **demo-worker**. Esa Lambda lo lee y lo borra, así que esa cola queda vacía.
4. **demo-orders-audit** recibe la misma copia y nadie la lee. Ahí quedan los mensajes para mirarlos.
5. **demo-publisher** manda un quinto pedido, `ord-lambda-1`, para probar una Lambda que escribe en el topic.
6. **demo-orders-dlq** espera mensajes que fallen 3 veces. Empieza vacía.

## Requisitos

- Docker Desktop en marcha.
- AWS CLI (`aws`).
- Python 3. Lo usa el paso que publica los pedidos.
- Terraform 1.5 o más nuevo.

En macOS, Terraform se instala desde el tap de HashiCorp:

```bash
brew tap hashicorp/tap
brew install hashicorp/tap/terraform
terraform version
```

## 1. Token de LocalStack

La imagen actual pide una cuenta, también en el plan Hobby (gratis para uso no comercial).

1. Crea la cuenta en [https://app.localstack.cloud](https://app.localstack.cloud).
2. Copia un Developer Auth Token desde [Auth Tokens](https://app.localstack.cloud/workspace/auth-tokens).
3. En la raíz de este repo:

```bash
cp .env.example .env
```

4. Pega el token en `LOCALSTACK_AUTH_TOKEN`. Ese archivo no se commitea.

## 2. Arrancar LocalStack

Desde la raíz del repo:

```bash
./scripts/up
```

Eso levanta el contenedor `localstack-main`. El gateway queda en `http://localhost:4566`.

Comprueba que está sano:

```bash
docker compose ps
curl -s http://localhost:4566/_localstack/health
```

La Web UI es [https://app.localstack.cloud](https://app.localstack.cloud). Conecta la instancia a `https://localhost.localstack.cloud:4566`. Desde ahí se ven IAM, Lambda, SQS y SNS.

Para pararlo:

```bash
./scripts/down
```

`PERSISTENCE=0` en `.env` significa que al bajar el contenedor se pierde lo que había dentro de LocalStack. Los archivos de Terraform siguen en el disco. Después de un `./scripts/up` hay que volver a hacer `terraform apply` para recrear los recursos.

En este Mac el socket de Docker está en `~/.docker/run/docker.sock`. `scripts/up` exporta `DOCKER_HOST` para que Compose lo encuentre. Hace falta montar ese socket para que Lambda pueda arrancar contenedores.

## 3. Crear los recursos con Terraform

Los `.tf` están en `terraform/`. Hay que ejecutar Terraform **dentro de esa carpeta**. Si lo corres en la raíz del repo, responde `No configuration files` porque ahí no hay archivos `.tf`.

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

- `terraform init` descarga los plugins de AWS y de zip. Se hace una vez, o cuando cambian los providers.
- `terraform plan` muestra lo que crearía. No crea nada.
- `terraform apply` lo crea. Confirma con `yes`.

Al final imprime los ARN de los roles, el ARN del topic y las URLs de las colas.

Para ver los pedidos que quedaron en la cola de auditoría, sigue dentro de `terraform/`:

```bash
../scripts/awslocal sqs receive-message \
  --queue-url "$(terraform output -raw audit_queue_url)" \
  --max-number-of-messages 5 \
  --visibility-timeout 0 \
  --message-attribute-names All
```

`scripts/awslocal` es el AWS CLI apuntando a `http://localhost:4566`, con la clave de prueba `test` y la región `us-east-1`.

## Qué es Terraform en este proyecto

Terraform no es el programa de los pedidos. Es la lista de “quiero este rol, esta cola, esta Lambda”. `terraform apply` lee esa lista y la crea en LocalStack. Anota lo creado en `terraform/terraform.tfstate`. La próxima vez no vuelve a crear lo que ya existe.

No hay nombres de archivo obligatorios. Terraform junta **todos** los `.tf` de la carpeta y los trata como una sola receta. Podrían llamarse de otra forma, o ir todos en un solo archivo. El orden de los archivos no importa. El orden de creación lo marcan las referencias: si una Lambda usa `aws_iam_role.worker.arn`, el rol se crea antes.

| Archivo | Qué hace |
|---|---|
| `versions.tf` | Pide Terraform >= 1.5, el provider AWS 5.x y el provider que hace los zip. |
| `provider.tf` | Apunta IAM, Lambda, SQS, SNS, STS y logs a `http://localhost:4566`. Define la región y la etiqueta `Project = localstack-demo`. |
| `iam.tf` | Crea los tres roles y lo que cada uno puede hacer. |
| `sqs.tf` | Crea las tres colas y el permiso para que SNS les escriba. |
| `sns.tf` | Crea el topic y lo suscribe a las dos colas. |
| `lambda.tf` | Empaqueta `lambda/*.py` y crea las dos funciones y el cable de `demo-orders` hacia `demo-worker`. |
| `messages.tf` | Publica los pedidos de `messages.json` e invoca `demo-publisher`. |
| `outputs.tf` | Imprime ARN y URLs al terminar. No crea recursos. |

`messages.json`, los `.py` y los `.zip` de `build/` no se ejecutan solos. Un `.tf` los lee o los empaqueta.

Orden real del `apply`:

1. Comprime las Lambdas en tu Mac y consulta la cuenta (`000000000000`).
2. Crea la cola fallida, la cola de auditoría, el topic y los roles de las Lambdas.
3. Crea `demo-orders` (necesita la cola fallida) y el rol lector (necesita el número de cuenta).
4. Crea las políticas de los roles y de las colas.
5. Crea las dos Lambdas.
6. Suscribe las colas al topic y conecta `demo-orders` con `demo-worker`.
7. Publica los cuatro pedidos y llama a `demo-publisher` con `ord-lambda-1`.
8. Imprime los outputs.

## Los dos documentos de un rol

Un rol tiene dos textos distintos.

El **Assume Role Policy** dice quién puede ponerse el rol. En `demo-lambda-publisher` dice que el servicio Lambda puede asumirlo (`sts:AssumeRole`). Eso es lo que muestra la Web UI en “Assume Role Policy Document”.

La **política adjunta** dice qué puede hacer después de ponérselo. Está en la pestaña de permisos:

- `demo-lambda-worker`, política `consume-orders`: leer y borrar mensajes de `demo-orders`, y escribir logs.
- `demo-lambda-publisher`, política `publish-events`: publicar solo en `demo-events`, y escribir logs.
- `demo-orders-reader`, política `read-audit`: mirar la cola de auditoría y consultar el topic. No puede publicar ni borrar.

## Código de las Lambdas

- `lambda/worker.py` recibe el evento de SQS, lee el pedido y lo escribe en los logs.
- `lambda/publisher.py` publica en el topic que Terraform le pasa por la variable `TOPIC_ARN`.

Si cambias un `.py` o `messages.json`, otro `terraform apply` desde `terraform/` vuelve a subir la función o a publicar los pedidos.

## Errores frecuentes

`No configuration files`**.** El comando se lanzó fuera de `terraform/`. Entra a esa carpeta y repítelo.

**El contenedor no arranca.** Revisa que Docker Desktop esté abierto y que `LOCALSTACK_AUTH_TOKEN` en `.env` no esté vacío.

`EntityAlreadyExists` **en el apply.** Esos nombres ya existen en LocalStack y Terraform no los tiene en su estado. Con la persistencia apagada, `./scripts/down`, `./scripts/up` y otro `terraform apply` dejan la cuenta limpia y la vuelven a crear.

## Trabajos con demanda

Una cola nueva, `demo-jobs`, recibe trabajos de un API Nest. Un subscriber en un cluster kind los consume, y KEDA sube o baja las réplicas según cuántos mensajes haya visibles. El circuito de pedidos (`demo-events`, `demo-orders`, las Lambdas) no cambia.

El API escucha `POST /jobs` y `GET /health`. El CronJob llama a ese mismo `POST` cada minuto con `{"type":"scheduled"}`. Un trabajo con `"type":"fail"` hace fallar al subscriber a propósito para que, al tercer intento, caiga en `demo-jobs-dlq`.

Desde la raíz, con LocalStack ya levantado:

```bash
cd terraform && terraform apply
cd ../jobs && bun install && bun test && docker build -t jobs-api:local .
cd ..
kind create cluster --config k8s/kind-config.yaml
kind load docker-image jobs-api:local --name localstack-jobs
helm repo add kedacore https://kedacore.github.io/charts
helm upgrade --install keda kedacore/keda --namespace keda --create-namespace
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/worker-deployment.yaml
kubectl apply -f k8s/scaledobject.yaml
kubectl apply -f k8s/cronjob.yaml
kubectl -n keda patch deployment keda-operator --type strategic --patch-file k8s/keda-operator-hostalias.yaml
```

El API queda en `http://127.0.0.1:3000`. Los pods llegan a LocalStack por `host.docker.internal`, que en Docker Desktop es `192.168.65.254`. Ese alias también va en el operador de KEDA, porque es quien lee la profundidad de la cola. Los pasos de comprobación están en `specs/001-keda-jobs/quickstart.md`.

## Spec Kit

[Spec Kit](https://github.com/github/spec-kit) es el flujo de GitHub para escribir una especificación antes de implementar. En este repo está instalado para Cursor.

El CLI `specify` 1.4.0 está instalado en la máquina. El proyecto ya fue inicializado: las plantillas viven en `.specify/` y los comandos de Cursor en `.cursor/skills/`.

Para instalarlo de nuevo en otra máquina hace falta `uv` y Python 3.11 o más nuevo:

```bash
uv tool install specify-cli --force --from git+https://github.com/github/spec-kit.git@v1.4.0
specify version
```

Desde la raíz de este repo, para volver a generar los archivos sin borrar el código de LocalStack ni Terraform:

```bash
specify init --here --force --non-interactive --integration cursor-agent --script sh
```

`--here` usa este directorio. `--force` mezcla los archivos en un directorio que ya tiene código. `--integration cursor-agent` instala las skills de Cursor. `--script sh` deja los scripts en bash.

Qué quedó en el repo:

| Ruta | Qué es |
|---|---|
| `.specify/memory/constitution.md` | Principios del proyecto. Empieza como plantilla. |
| `.specify/templates/` | Plantillas de spec, plan, tareas y checklist. |
| `.specify/scripts/bash/` | Scripts que usan las skills para crear specs y planes. |
| `.specify/workflows/speckit/` | Definición del flujo. |
| `.cursor/skills/speckit-*/SKILL.md` | Comandos que se invocan en el chat de Cursor. |

`.specify/feature.json` es estado local de la feature activa y no se comparte. Ya está ignorado por `.specify/.gitignore`.

En el chat de Cursor, en este proyecto, el orden es:

1. `/speckit-constitution` fija los principios del repo.
2. `/speckit-specify` escribe la especificación de un cambio a partir de una descripción.
3. `/speckit-clarify` es opcional. Hace preguntas si la spec es ambigua. Va antes del plan.
4. `/speckit-plan` arma el plan de implementación.
5. `/speckit-checklist` es opcional. Revisa que la spec esté completa.
6. `/speckit-tasks` parte el plan en tareas.
7. `/speckit-analyze` es opcional. Cruza spec, plan y tareas antes de implementar.
8. `/speckit-implement` ejecuta las tareas.
9. `/speckit-converge` compara el código con la spec y agrega el trabajo que falta.

Estos comandos no sustituyen a Terraform ni a LocalStack. Describen el próximo cambio. La infraestructura de este repo se sigue creando con `./scripts/up` y `terraform apply`.
