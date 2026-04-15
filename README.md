# AI Workflow Copilot

A production-style starter for an AI Engineer portfolio project.

## What is included
- FastAPI backend
- PostgreSQL + pgvector schema
- Document upload, parsing, chunking, embeddings
- LangGraph agent flow: planner → retriever → draft → reviewer
- OpenAI / Azure OpenAI provider switch
- Langfuse tracing for each chat request
- Evals scaffolding

## Run locally
1. Copy `backend/.env.example` to `backend/.env`
2. Fill in either OpenAI or Azure OpenAI credentials
3. Fill in Langfuse keys if you want tracing
4. Run Docker Compose from `infra/docker-compose.yml`
5. Start the backend with uvicorn

## Agent flow
The request passes through:
- planner node
- retrieval node
- draft node
- review node

Each important step is traced so you can show the full path in interviews.
