# AI Inference Rate Limiter Service

## Overview
A service that manages and enforces rate limiting for AI inference requests to prevent resource exhaustion and ensure fair usage.

## Highllights
- Sliding window log algorithm ( Accuracy and Implementation)
- Atomicity
- Production Standards

## Getting Started
Follow the below steps to run and test locally

## Pre-requisites
- Python and Docker installed in the system

## Run (Execution) Steps
 - bash cd /ai_inference_rate_limiter_svc
 - bash docker compose up --build -d
 - health cehck: bash curl http://localhost:8000/health
### Expected: {"status": "ok", "dependencies": "redis_ok"}

## Testing
- send the requests using below command
    "python
    import requests, json
    URL = "http://localhost:8000/api/v1/inference/allow"
    for i in range(100):
        requests.post(URL, data=json.dumps({"user_id": "test_user_A", "model_id": "test"}), headers={'Content-Type': 'application/json'})
    print("100 requests sent. Log is full.")"
- this command will be rejected and retruns 429 error
    "bash curl -X POST "http://localhost:8000/api/v1/inference/allow" \
         -H "Content-Type: application/json" \
         -d '{"user_id": "test_user_A", "model_id": "test"}' -v "

## To stop the containers
- bash docker compose down
