# ============================================================================
# PLACEHOLDER Dockerfile — authored by the DevOps agent, 2026-09-12
# ============================================================================
# Purpose: prove out the CI/CD pipeline (build -> push to ECR -> deploy to
# Lambda) *now*, before Backend Dev's real FastAPI app exists. Architect is
# still building the schema Backend Dev's app will be written against, so
# there is nothing real to containerize yet — but the pipeline needs
# something to build.
#
# THIS IS NOT THE REAL APPLICATION. Per backend/CLAUDE.md, this file is
# Backend Dev's to own ("Dockerfile ... You own its contents; DevOps agent
# builds/pushes/deploys it, doesn't edit it."). DevOps is authoring this one
# placeholder version only because nothing exists here yet and the pipeline
# has to be validated end-to-end. Backend Dev: replace the application code
# below with the real app (app/main.py, routers, etc.) — the base image and
# overall CMD/handler structure can likely stay as-is, since that part is
# dictated by how AWS Lambda container images work, not by app content.
#
# This is an honest, minimal "hello world" FastAPI + Mangum app: it starts,
# and it responds 200 on GET /health (matches the public, no-auth /health
# route already documented in backend/CLAUDE.md's "Public Routes" section).
# ============================================================================

# AWS-provided base image for Lambda Python container images (Python 3.12,
# per root CLAUDE.md stack). Sets WORKDIR=/var/task (== $LAMBDA_TASK_ROOT)
# and bakes in the Lambda Runtime Interface Client / entrypoint already —
# do not override ENTRYPOINT.
FROM public.ecr.aws/lambda/python:3.12

# Placeholder-only dependencies. Not added to backend/requirements.txt: that
# file is Architect/Backend Dev's to own (see its own header comment), and
# DevOps doesn't want to leave app-layer deps behind for Backend Dev to
# clean up. Backend Dev's real requirements.txt (fastapi, mangum, boto3,
# stripe, etc. per backend/CLAUDE.md "Stack") supersedes this entirely.
RUN pip install --no-cache-dir fastapi==0.111.0 mangum==0.17.0

# Placeholder app, written directly into the image so nothing is left behind
# under backend/app/ (that tree belongs to Architect/Backend Dev). Replace
# this whole RUN block with a real `COPY app/ ${LAMBDA_TASK_ROOT}/app/` (or
# similar) once app/main.py exists.
RUN printf '%s\n' \
    'from fastapi import FastAPI' \
    'from mangum import Mangum' \
    '' \
    'app = FastAPI()' \
    '' \
    '@app.get("/health")' \
    'def health():' \
    '    return {"status": "ok"}' \
    '' \
    'handler = Mangum(app)' \
    > "${LAMBDA_TASK_ROOT}/main.py"

# package_type = "Image" Lambda functions have no separate "handler" config —
# CMD here *is* the handler, in "<module>.<callable>" form (see
# infra/CLAUDE.md "Lambda + API Gateway" — no runtime/handler args needed).
CMD ["main.handler"]
