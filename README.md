# Prompt Engineering & Evaluation Studio

Portfolio-grade reference implementation for testing prompt variants across LLM adapters, validating structured output, scoring responses, and aggregating experiment analytics.

## Architecture

`Client -> Java 21 / Spring Boot Gateway -> Python / FastAPI Evaluation Engine -> Model Adapters -> Metrics + Experiment Store`

The included `mock-balanced` and `mock-strict` adapters make the repository runnable without API keys. `mock_model()` is deliberately isolated so Azure OpenAI, OpenAI, Hugging Face, vLLM, or other adapters can be added without changing the experiment API.

## Features

- Compare N prompts x N models x N evaluation examples.
- `{{input}}` prompt templating.
- Text and JSON output modes.
- Required-key structured-output validation.
- Reference similarity/accuracy scoring.
- JSON validity and schema-pass rates.
- Latency and response-size metrics.
- Per-case results plus grouped experiment summaries.
- Experiment lookup and aggregate analytics endpoint.
- Python service plus Java enterprise gateway.
- Offline deterministic model adapters for CI/testing.

## Run with Docker

```bash
docker compose up --build
```

Gateway: `http://localhost:8080`; Python/OpenAPI: `http://localhost:8000/docs`.

## Example experiment

```bash
curl -X POST http://localhost:8080/api/v1/experiments \
-H 'Content-Type: application/json' \
-d '{
  "name":"sentiment-json",
  "models":["mock-balanced","mock-strict"],
  "prompts":[
    {"name":"basic","template":"Classify sentiment. INPUT: {{input}}"},
    {"name":"strict","template":"Return only JSON with answer and sentiment. INPUT: {{input}}"}
  ],
  "dataset":[
    {"input":"I love this product, it is excellent.","expected":{"answer":"I love this product, it is excellent.","sentiment":"positive"}}
  ],
  "output_mode":"json",
  "json_required_keys":["answer","sentiment"]
}'
```

## Local Python development

```bash
cd python-service
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
pytest -q
```

## Local Java development

Requires Java 21 and Maven.

```bash
cd java-service
mvn spring-boot:run
```

## API

- `POST /api/v1/experiments` — execute an experiment.
- `GET /api/v1/experiments/{id}` — retrieve its detailed results.
- `GET /api/v1/analytics` — aggregate execution counts.
- `GET /health` — Python service health.

## Production extensions

For a production version, replace the in-memory store with PostgreSQL/ClickHouse, add asynchronous experiment jobs through Kafka, distributed workers, Azure OpenAI/local-model adapters, JSON Schema/Pydantic structured-output validation, semantic and LLM-as-judge metrics, pairwise ranking, groundedness/safety evaluators, confidence intervals and significance testing, prompt/model versioning, MLflow-style experiment lineage, RBAC/Entra ID, tenant quotas, OpenTelemetry traces, dashboards, Kubernetes deployment, cost/token accounting, caching, CI regression gates, and human annotation workflows.

A strong system-design story is: **Prompt Registry -> Experiment Scheduler -> Model Gateway -> Evaluation Workers -> Metrics Store -> Analytics API/UI**, with reproducible dataset/model/prompt versions and automated quality gates before production rollout.
