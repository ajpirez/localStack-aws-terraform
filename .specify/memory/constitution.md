<!--
Sync Impact Report
- Version change: unversioned template → 1.0.0
- Modified principles: none (initial ratification)
- Added sections:
  - Core Principles I–V
  - Restricciones del entorno
  - Flujo de trabajo
  - Governance
- Removed sections: none
- Follow-up TODOs: none
-->

# LocalStack Constitution

## Core Principles

### I. LocalStack es el único AWS

Todo cliente, prueba y recurso de este repo MUST apuntar a LocalStack en
`http://localhost:4566`, región `us-east-1`, con la clave de prueba `test`.
MUST NOT usar credenciales ni endpoints del AWS real. El contenedor MUST
arrancar con `./scripts/up` y parar con `./scripts/down`.

Rationale: el repo existe para ensayar IAM, Lambda, SQS y SNS sin una cuenta
de AWS de producción.

### II. Terraform declara la infraestructura

Los roles, colas, topics, suscripciones, funciones y el cable SQS → Lambda
MUST vivir en `terraform/*.tf`. El código de las funciones MUST vivir en
`lambda/*.py` y publicarse como zip mediante `terraform apply`, ejecutado
desde `terraform/`. MUST NOT recrear esos recursos con scripts sueltos.

Rationale: el estado de Terraform es la memoria de lo creado. Un script
paralelo deja recursos que Terraform no conoce.

### III. Cada cambio nuevo empieza por una spec

Una modificación de comportamiento MUST empezar en `/speckit-specify` y
seguir el flujo de Spec Kit hasta `/speckit-implement`. La constitución y las
specs existentes MUST leerse antes de planear. Un cambio que solo corrige
redacción o formato MAY omitir una spec nueva.

Rationale: Spec Kit está instalado para que el próximo cambio tenga
especificación, plan y tareas antes del código.

### IV. Cada rol tiene dos documentos y el mínimo permiso

El documento de confianza MUST decir solo quién puede asumir el rol. La
política adjunta MUST decir solo las acciones y los ARN que ese rol usa.
`demo-lambda-worker` MUST limitarse a consumir `demo-orders` y escribir logs.
`demo-lambda-publisher` MUST limitarse a publicar en `demo-events` y escribir
logs. `demo-orders-reader` MUST limitarse a leer `demo-orders-audit` y
consultar el topic.

Rationale: el documento de confianza no concede `sns:Publish` ni acceso a
colas. Mezclarlos oculta qué puede hacer el rol.

### V. Cada ejecución debe poder rastrearse

`demo-publisher` MUST devolver el `messageId` que responde SNS. `demo-worker`
MUST escribir en logs el `orderId` de cada mensaje procesado. Un mensaje que
falle MUST permanecer en `demo-orders` hasta 3 recepciones y luego MUST pasar
a `demo-orders-dlq`. `demo-orders-audit` MUST conservar una copia sin
consumidor. La entrega cruda a SQS MUST mantenerse; el enlace con el topic
se comprueba en la suscripción y en la política de la cola.

Rationale: SNS no guarda los mensajes. Sin el `messageId`, el log y la cola
de auditoría no hay forma de seguir el recorrido.

## Restricciones del entorno

- Docker Desktop MUST estar en marcha. En este Mac el socket MUST montarse
  desde `~/.docker/run/docker.sock`.
- `LOCALSTACK_AUTH_TOKEN` MUST vivir solo en `.env`. MUST NOT commitearse.
- `PERSISTENCE=0` es la configuración vigente. Reiniciar el contenedor borra
  los recursos. Después de `./scripts/up` MUST repetirse `terraform apply`.
- La cuenta local es `000000000000`. Los comandos de inspección MUST usar
  `scripts/awslocal`.
- Spec Kit MUST permanecer en `.specify/` y `.cursor/skills/`, integración
  `cursor-agent`, scripts bash, CLI `specify` 1.4.0.
- La guía de operación MUST mantenerse en `readme.md`.

## Flujo de trabajo

El orden para un cambio nuevo es:

1. `/speckit-constitution` solo si cambia una regla de este documento.
2. `/speckit-specify` describe el cambio.
3. `/speckit-clarify` cuando la spec deje una decisión abierta.
4. `/speckit-plan` define los archivos y recursos afectados.
5. `/speckit-checklist` revisa que la spec esté completa.
6. `/speckit-tasks` parte el plan en tareas.
7. `/speckit-analyze` cruza spec, plan y tareas.
8. `/speckit-implement` cambia el código.
9. `/speckit-converge` compara el resultado con la spec.

Los pasos 3, 5, 7 y 9 son opcionales. Implementar MUST ocurrir después de
spec, plan y tareas. `terraform apply` MUST lanzarse desde `terraform/`.

## Governance

Esta constitución prevalece sobre atajos de implementación. Una enmienda MUST
editar este archivo, subir la versión semántica y actualizar la fecha de
enmienda. MAJOR rompe una regla ya ratificada. MINOR agrega una regla.
PATCH corrige redacción sin cambiar la obligación.

Una spec o un plan que toque IAM, mensajería o el runtime MUST indicar qué
principio cumple. El informe de impacto al inicio de este archivo es material
de revisión y MUST quitarse antes de commitear la enmienda.

**Version**: 1.0.0 | **Ratified**: 2026-11-13 | **Last Amended**: 2026-11-13
