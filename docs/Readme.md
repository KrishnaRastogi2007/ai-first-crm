# Production Architecture

                         ┌──────────────────────┐
                         │    React + Redux     │
                         │      Frontend        │
                         └──────────┬───────────┘
                                    │
                              HTTPS / REST
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │    Reverse Proxy     │
                         │    / API Gateway     │
                         └──────────┬───────────┘
                                    │
                                    ▼
              ╔══════════════════════════════════════════╗
              ║              FASTAPI BACKEND             ║
              ║                                          ║
              ║  Authentication / Authorization         ║
              ║               │                          ║
              ║               ▼                          ║
              ║         API / Controllers                ║
              ║               │                          ║
              ║       ┌───────┴────────┐                 ║
              ║       │                │                 ║
              ║       ▼                ▼                 ║
              ║   Normal CRUD       AI Chat              ║
              ║       │                │                 ║
              ║       │                ▼                 ║
              ║       │          ┌─────────────┐         ║
              ║       │          │  LangGraph  │         ║
              ║       │          │    Agent    │         ║
              ║       │          └──────┬──────┘         ║
              ║       │                 │                ║
              ║       │            Groq / Gemma          ║
              ║       │                 │                ║
              ║       │                 ▼                ║
              ║       │          ┌──────────────┐        ║
              ║       │          │ 6 CRM Tools  │        ║
              ║       │          └──────┬───────┘        ║
              ║       │                 │                ║
              ║       └────────┬────────┘                ║
              ║                ▼                         ║
              ║          Service Layer                   ║
              ║                │                         ║
              ║                ▼                         ║
              ║        Repository Layer                 ║
              ╚════════════════┬═════════════════════════╝
                               │
                ┌──────────────┼───────────────┐
                ▼              ▼               ▼
          PostgreSQL         Redis          Object Storage
          Main DB            Cache          Voice/Files
                │
                ▼
           Audit Logs


       ┌─────────────────────────────────────────────┐
       │          Background Workers                 │
       │                                             │
       │ Voice transcription                         │
       │ AI summarization                            │
       │ Notifications                               │
       │ Follow-up processing                        │
       └─────────────────────────────────────────────┘

       ┌─────────────────────────────────────────────┐
       │             Observability                   │
       │ Logs + Metrics + Tracing + Error Monitoring│
       └─────────────────────────────────────────────┘

 
---

## Explanation of Components

### 1. Client Layer (Frontend)
- **React + Redux**: Handles the dynamic Single Page Application (SPA). Redux manages global client-side state (user sessions, cached CRM data, UI flags) to ensure a snappy user experience.
- **Communication**: Talks exclusively to the backend via HTTPS/REST, ensuring encrypted data transfer. It does not connect directly to databases or workers.

### 2. Entry Point & Security (Reverse Proxy / API Gateway)
- **Role**: Sits at the edge of your infrastructure. Examples include Nginx, Traefik, or AWS API Gateway.
- **Functions**:
  - SSL/TLS Termination (handles HTTPS certificates).
  - Load Balancing (distributes incoming traffic across multiple FastAPI server instances).
  - Rate Limiting (prevents DDoS or API abuse).
  - Static File Serving (serves the built React `index.html` and JS bundles directly, offloading this from the backend).
- **Request Routing**: Proxies all `/api/*` requests to the FastAPI backend.

### 3. The Core Backend (FastAPI)
This is the engine room, written in Python, leveraging `async`/`await` for high concurrency. It follows a strict Layered Architecture:

- **Authentication / Authorization Layer**:
  - Validates incoming JWT (JSON Web Tokens) or OAuth2 sessions.
  - Implements RBAC (Role-Based Access Control)—e.g., checking if a sales rep has permission to view a "Enterprise" tier deal before the request even hits the controllers.

- **API / Controllers (Routers)**:
  - The HTTP entry points. They parse request bodies, validate input via Pydantic schemas, and return structured JSON responses.
  - They are deliberately thin; they call the Service Layer and translate HTTP errors into proper status codes (200, 404, 403).

- **The Business Logic Fork (The "Brain")**:
  - **Normal CRUD Path**: Handles standard operations (creating contacts, updating deal stages, fetching user profiles). Simple, fast, synchronous database lookups.
  - **AI Chat Path (LangGraph Agent)**: This is the centerpiece. Instead of a standard controller, this endpoint passes the user's prompt to a LangGraph Agent.
    - **LangGraph**: Orchestrates the conversational flow. It manages the state of the conversation, loops between reasoning and acting, and decides when to stop.
    - **Groq / Gemma**: The underlying Large Language Models (LLMs). Groq provides ultra-low-latency inference (perfect for real-time chat), while Gemma (Google's open model) might be used for fine-tuned, cost-effective reasoning.
    - **The 6 CRM Tools**: This is the Agent's "hands". The LLM cannot touch the database directly; it outputs structured JSON to call these specific tools. Examples likely include:
      - `search_contacts(keyword)`
      - `create_opportunity(details)`
      - `log_interaction(contact_id, notes)`
      - `schedule_follow_up(datetime)`
      - `get_sales_analytics(timeframe)`
      - `send_email_draft(content)`
    - The Agent decides which tool to use, extracts the parameters, and calls it.

- **Service Layer**:
  - Houses the pure business logic.
  - For the AI path, this orchestrates the Agent's tool calls. For CRUD, it applies domain rules (e.g., "Deal amount cannot be negative" or "Status must move from Lead → Qualified → Closed"). It acts as an intermediary between the Controllers and the Repository.

- **Repository Layer**:
  - The Data Access Object (DAO) pattern. These classes contain all the SQLAlchemy or raw SQL queries. By abstracting the database logic here, you can easily swap databases or cache strategies without affecting the Service Layer.

### 4. Data Persistence Layer
The architecture wisely uses the **Polyglot Persistence** pattern, choosing the right database for the right job:

- **PostgreSQL (Main DB)**: The Source of Truth. Stores relational, structured data: Users, Accounts, Deals, Tasks, and the Audit Logs (which are critical for compliance and are stored here for permanent retention).
- **Redis (Cache & Session Store)**:
  - **Caching**: Stores frequently accessed, slow-to-compute data (e.g., dashboard KPI aggregations) to reduce PostgreSQL load.
  - **Rate Limiting Counter**: Tracks API request counts per user/IP.
  - **Pub/Sub or Queue Broker**: Acts as the communication bridge for the Background Workers.
- **Object Storage (S3/MinIO)**: Stores unstructured data. Voice call recordings, uploaded PDFs, profile pictures, and exported reports. The database only stores the `S3://bucket/path/file.mp3` string.

### 5. Background Workers (Async Processing)
AI workflows are notoriously slow (transcription takes seconds, LLM summarization takes seconds). This architecture offloads these to separate worker processes (using Celery, RQ, or FastAPI's `BackgroundTasks` with Redis).

- **Voice Transcription**: A worker takes the audio file path from S3, passes it to a model (e.g., Whisper), and saves the resulting text back to the main DB.
- **AI Summarization**: After a meeting log is created, a worker asynchronously summarizes the text and tags key action items.
- **Notifications**: Sends transactional emails (via SendGrid/SES) or push notifications to the React frontend (via WebSockets/SSE) without blocking the API response.
- **Follow-up Processing**: If a user says "Remind me about this in 2 hours", a worker schedules a delayed job. When the time hits, it triggers a notification.

### 6. Observability (The Watchdog)
This cross-cutting layer is essential for debugging and performance in production:

- **Logs**: Structured JSON logs (using `structlog`) shipped to ELK or Datadog for searching.
- **Metrics (Prometheus)**: Tracks request latency, error rates, database connection pool usage, and AI token consumption. Used to auto-scale replicas.
- **Tracing (Jaeger/OpenTelemetry)**: Implements distributed tracing. You can trace a single user request: React → Gateway → FastAPI Controller → LangGraph Agent → Tool Service → PostgreSQL → Response. This highlights exactly where latency occurs.
- **Error Monitoring (Sentry)**: Automatically captures unhandled Python exceptions and provides full stack traces with environment snapshots.

---

## How a Complete Request Flows (Example: Voice-to-Action)

To truly understand this, let's trace a **Voice Note Upload** where a rep says, *"Create a follow-up task for Acme Corp regarding the contract"*:

1. **Frontend**: Rep records voice. React uploads the `.mp3` chunk to the FastAPI `/api/voice/upload` endpoint.
2. **FastAPI Controller**: Stores the `.mp3` in Object Storage. It immediately publishes a job `{"file_id": "123", "user_id": "rep_1"}` to Redis Queue and returns `202 Accepted` to the frontend (so the UI doesn't freeze).
3. **Background Worker (Transcription)**: Picks up the job, streams the audio from S3, transcribes it to text *"Create follow-up for Acme Corp contract"*. It saves this text to PostgreSQL and publishes a new job to the AI Processing Queue.
4. **Background Worker (AI Agent)**: Takes the text, passes it to the LangGraph Agent with the prompt context.
5. **LangGraph Agent**:
   - Calls the LLM (Groq).
   - The LLM decides it needs **Tool #3**: `search_contacts("Acme Corp")` to find the Account ID.
   - Agent calls the Service Layer, which queries PostgreSQL.
   - Agent gives the Account ID back to the LLM.
   - The LLM decides it needs **Tool #4**: `create_task(account_id, "Follow-up on contract", due_date)`.
   - The Service Layer validates the input and the Repository inserts the new Task row into PostgreSQL (which also triggers an Audit Log entry).
   - Agent returns the final confirmation text to the Worker.
6. **Background Worker (Notification)**: Pushes a WebSocket message to the React frontend saying *"Task created successfully for Acme Corp"*.
7. **Observability**: Throughout this flow, OpenTelemetry traces span the Gateway, Worker, and DB, while Sentry watches for exceptions.

---

## Strengths of this Architecture

- **Scalability**: Web servers (FastAPI) and Background Workers can be scaled independently. If your AI usage spikes, you spin up more Workers, not more Web servers.
- **Resilience**: If the LLM API (Groq) goes down, the Workers retry or fail gracefully without crashing the main CRUD APIs.
- **Maintainability**: The strict Controller–Service–Repository separation makes unit testing trivial. You can mock the LLM to test the business logic.
- **Security**: The Agent is tool-bound—the LLM cannot execute arbitrary code or SQL; it can only call the 6 pre-approved CRM tools, completely preventing prompt injection from bypassing database constraints.

# Backend Folder Structure

backend/
│
├── app/
│   │
│   ├── main.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── logging.py
│   │   ├── exceptions.py
│   │   └── dependencies.py
│   │
│   ├── db/
│   │   ├── database.py
│   │   ├── base.py
│   │   └── migrations/
│   │
│   ├── api/
│   │   ├── router.py
│   │   │
│   │   ├── v1/
│   │   │   ├── auth.py
│   │   │   ├── chat.py
│   │   │   ├── hcps.py
│   │   │   ├── interactions.py
│   │   │   ├── followups.py
│   │   │   └── users.py
│   │   │
│   │   └── middleware/
│   │       ├── auth.py
│   │       ├── rate_limit.py
│   │       └── request_id.py
│   │
│   ├── agents/
│   │   └── hcp_agent/
│   │       ├── graph.py
│   │       ├── state.py
│   │       ├── nodes.py
│   │       ├── routing.py
│   │       ├── prompts.py
│   │       └── tool_registry.py
│   │
│   ├── tools/
│   │   ├── log_interaction.py
│   │   ├── edit_interaction.py
│   │   ├── search_hcp.py
│   │   ├── interaction_history.py
│   │   ├── follow_up.py
│   │   └── summarize_interaction.py
│   │
│   ├── modules/
│   │   │
│   │   ├── auth/
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   └── repository.py
│   │   │
│   │   ├── hcp/
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   └── repository.py
│   │   │
│   │   ├── interaction/
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   └── repository.py
│   │   │
│   │   └── followup/
│   │       ├── models.py
│   │       ├── schemas.py
│   │       ├── service.py
│   │       └── repository.py
│   │
│   ├── integrations/
│   │   ├── groq.py
│   │   ├── storage.py
│   │   └── transcription.py
│   │
│   ├── workers/
│   │   ├── tasks.py
│   │   └── queue.py
│   │
│   └── audit/
│       ├── models.py
│       ├── service.py
│       └── repository.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── agent/
│
├── alembic/
│
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── README.md
└── pyproject.toml


1. Complete Structure — Big Picture

Tumhara backend:

backend/
│
├── app/
│
├── tests/
│
├── alembic/
│
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── README.md
└── pyproject.toml

Isko beginner language mein:

Folder/File	Simple Meaning
app/	Actual application ka code
tests/	Application ko test karne ka code
alembic/	Database changes/migrations
.env	Secret/configuration values
.env.example	Dusre developer ko batata hai kaunse environment variables chahiye
.gitignore	Git ko batata hai kaunsi files upload nahi karni
requirements.txt	Python dependencies
Dockerfile	Backend ka Docker image banane ke instructions
docker-compose.yml	Multiple services ko saath run karne ke instructions
README.md	Project documentation
pyproject.toml	Python project/tool configuration
2. app/ — Sabse Important Folder
app/

Is folder ke andar actual backend application hai.

Iske andar hum different responsibilities divide karenge:

app/
├── core/
├── db/
├── api/
├── agents/
├── tools/
├── modules/
├── integrations/
├── workers/
└── audit/

Ab ek-ek karke.

3. main.py — Backend ka Starting Point
app/
└── main.py

Ye application ka entry point hai.

Simple example:

from fastapi import FastAPI

app = FastAPI()

Jab tum run karoge:

uvicorn app.main:app

toh Python:

app/
 ↓
main.py
 ↓
app object

ko find karega.

main.py mein kya rahega?

Generally:

FastAPI application
Routers
Middleware
Exception handlers
Startup/shutdown configuration

Lekin business logic nahi.

4. core/ — Application ki Basic/Global Settings
core/
├── config.py
├── security.py
├── logging.py
├── exceptions.py
└── dependencies.py

core ko tum application ka foundation samajh sakte ho.

4.1 config.py
core/config.py

Yahan application ki configuration aayegi.

Example:

DATABASE_URL
GROQ_API_KEY
JWT_SECRET
REDIS_URL

Flow:

.env
 ↓
config.py
 ↓
Application

Example:

GROQ_API_KEY = "..."

ko code mein hardcode karne ke bajaye .env se load karenge.

5. security.py
core/security.py

Security-related functionality.

Example:

Password hashing
JWT token
Token validation
Authentication helpers
Authorization helpers

Flow:

User
 ↓
Login
 ↓
JWT Token
 ↓
API Request
 ↓
security.py
 ↓
Authenticated User
6. logging.py
core/logging.py

Production application mein debugging ke liye logs chahiye.

Instead of:

print("something happened")

hum proper logging use karenge.

Example:

INFO
WARNING
ERROR

Aur useful information:

request_id
user_id
endpoint
execution time
error
7. exceptions.py
core/exceptions.py

Application mein different errors aa sakte hain.

Example:

HCPNotFound
InteractionNotFound
Unauthorized
DatabaseError
LLMError
ValidationError

In errors ko properly define/handle karne ke liye ye file useful hai.

Instead of har jagah random:

raise Exception()

hum controlled errors use kar sakte hain.

8. dependencies.py
core/dependencies.py

FastAPI dependencies yahan rakhi ja sakti hain.

Example:

Get current user
Get database session
Check permissions

For example:

API Request
    ↓
get_current_user()
    ↓
User
9. db/ — Database Infrastructure
db/
├── database.py
├── base.py
└── migrations/

Ye folder database se connection/setup related code ke liye hai.

10. database.py
db/database.py

Ye PostgreSQL ke saath connection establish/manage karne ke liye hai.

Basic flow:

FastAPI
   ↓
SQLAlchemy
   ↓
PostgreSQL

Yahan database engine/session setup hoga.

11. base.py
db/base.py

SQLAlchemy ke database models ke liye common base/configuration rakh sakte hain.

Conceptually:

Database Models
      ↓
SQLAlchemy Base
      ↓
PostgreSQL Tables
12. migrations/
db/migrations/

Database schema ke changes track karne ke liye migrations hoti hain.

Lekin ek correction: tumhare structure mein already root level par:

alembic/

hai.

Production project mein main recommend karunga ki Alembic ki actual migration files ek hi jagah rakho, duplicate db/migrations/ nahi.

Better:

app/
└── db/
    ├── database.py
    └── base.py

alembic/
├── versions/
├── env.py
└── alembic.ini

So db/migrations/ hata sakte ho.

13. api/ — Front Door of Backend
api/
├── router.py
│
├── v1/
│   ├── auth.py
│   ├── chat.py
│   ├── hcps.py
│   ├── interactions.py
│   ├── followups.py
│   └── users.py
│
└── middleware/
    ├── auth.py
    ├── rate_limit.py
    └── request_id.py

API ko tum backend ka reception/front door samjho.

Frontend backend se directly service/repository ko call nahi karega.

Frontend:

React
 ↓
API
 ↓
Backend
14. router.py
api/router.py

Ye different API routers ko combine karega.

For example:

/auth
/chat
/hcps
/interactions
/followups
/users

ko main application se connect karega.

15. v1/ — API Version
api/v1/

Hum APIs ko version kar rahe hain.

Example:

/api/v1/hcps
/api/v1/interactions
/api/v1/chat

Future mein API change karni pade:

/api/v2/interactions

bana sakte hain.

Isse purana frontend immediately break nahi hota.

16. auth.py
api/v1/auth.py

Authentication endpoints.

Example:

POST /login
POST /register
POST /refresh-token
17. chat.py
api/v1/chat.py

Ye tumhare AI Assistant ka endpoint hoga.

Example:

POST /api/v1/chat

Flow:

React
 ↓
/chat
 ↓
LangGraph Agent
 ↓
LLM
 ↓
Tools
18. hcps.py

HCP related APIs.

Example:

GET /hcps
GET /hcps/{hcp_id}
19. interactions.py

Interaction related APIs.

Example:

POST /interactions
GET /interactions/{id}
PUT /interactions/{id}
20. followups.py

Follow-up related APIs.

Example:

POST /followups
GET /followups
PUT /followups/{id}
21. users.py

Users related endpoints.

Example:

GET /users/me
GET /users/{id}

depending on permissions.

22. middleware/

Middleware ko simple language mein:

Har request ke around automatically chalne wala common code.

Example:

Request
 ↓
Middleware
 ↓
API
 ↓
Response
 ↓
Middleware
 ↓
Client
23. auth.py Middleware

Authentication-related request processing.

24. rate_limit.py

Ek user bahut zyada requests na bhej sake.

Especially:

POST /chat

LLM calls expensive ho sakti hain.

Example concept:

User → 100 requests/second

Rate limiter request reject/throttle kar sakta hai.

25. request_id.py

Har request ko unique ID dena.

Example:

request_id = abc-123

Agar error aaya toh logs mein:

request_id=abc-123

search karke poori request trace kar sakte ho.

26. agents/ — AI Brain

Ab project ka sabse important AI part.

agents/
└── hcp_agent/
    ├── graph.py
    ├── state.py
    ├── nodes.py
    ├── routing.py
    ├── prompts.py
    └── tool_registry.py

Tumhara LangGraph agent yahan rahega.

27. state.py
agents/hcp_agent/state.py

LangGraph ko state chahiye.

State ko simple language mein:

Agent ki current working information/memory.

Example:

user_message
conversation_history
user_id
hcp_id
interaction_id
intent
tool_result
needs_confirmation
final_response

Imagine user bolta hai:

"Dr Sharma ki recent interaction history dikhao."

State gradually:

user_message
      ↓
intent = interaction_history
      ↓
hcp = Dr Sharma
      ↓
hcp_id = 123
      ↓
tool_result
      ↓
final_response
28. graph.py
agents/hcp_agent/graph.py

Yahan actual LangGraph workflow define hoga.

Concept:

START
 ↓
Agent
 ↓
Tool needed?
 ├── NO → Response → END
 │
 └── YES
       ↓
      Tool
       ↓
      Agent
       ↓
    Response
       ↓
      END

Ye LangGraph ka actual graph hai.

29. nodes.py

Graph ke individual nodes.

Example:

agent_node
tool_node
confirmation_node
response_node

Node ka simple meaning:

Graph ke andar ek processing step.

30. routing.py

Ye decide karega:

Next step kya hoga?

Example:

LLM bolta hai:

search_hcp

Routing:

Agent
 ↓
search_hcp

LLM bolta hai:

follow_up

Routing:

Agent
 ↓
follow_up
31. prompts.py

LLM ko instructions.

Example:

You are an AI assistant for a life-science CRM.

You can use the following tools:
...

Yahan agent ka system prompt/instructions maintain karenge.

32. tool_registry.py

Ye available tools ko organize/register karega.

Tumhare 6 tools:

1. log_interaction
2. edit_interaction
3. search_hcp
4. interaction_history
5. follow_up
6. summarize_interaction

Agent ko available tools ka knowledge yahan se milega.

33. tools/ — AI ke Hands

Ye concept bahut important hai.

Agar:

LangGraph = Brain

toh:

Tools = Hands

Tumhare tools:

tools/
├── log_interaction.py
├── edit_interaction.py
├── search_hcp.py
├── interaction_history.py
├── follow_up.py
└── summarize_interaction.py
34. log_interaction.py

User:

"Log meeting with Dr Sharma. We discussed Product X."

Agent:

LLM
 ↓
log_interaction tool

Tool:

Interaction Service
 ↓
Repository
 ↓
PostgreSQL

LLM extraction/summarization mein help kar sakta hai, but final data validation/business rules service layer mein hone chahiye.

35. edit_interaction.py

User:

"Change the sentiment of that interaction to positive."

Flow:

LLM
 ↓
edit_interaction
 ↓
Interaction Service
 ↓
Repository
 ↓
PostgreSQL
36. search_hcp.py

User:

"Find Dr Sharma."

Tool:

search_hcp
 ↓
HCP Service
 ↓
HCP Repository
 ↓
PostgreSQL
37. interaction_history.py

User:

"Show my recent interactions with Dr Sharma."

interaction_history
 ↓
Interaction Service
 ↓
Repository
 ↓
PostgreSQL
38. follow_up.py

User:

"Schedule a follow-up with Dr Sharma next Monday."

follow_up
 ↓
Follow-up Service
 ↓
Repository
 ↓
PostgreSQL
39. summarize_interaction.py

User:

"Summarize this interaction."

Flow:

Interaction
 ↓
Summarization Tool
 ↓
LLM
 ↓
Summary

Agar summary database mein save karni ho:

LLM
 ↓
Interaction Service
 ↓
Repository
 ↓
PostgreSQL
40. Very Important — Tool directly DB ko access nahi karega

Avoid:

Tool
 ↓
SQL
 ↓
Database

Instead:

Tool
 ↓
Service
 ↓
Repository
 ↓
Database

Kyun?

Because Tool ka kaam AI ko action provide karna hai.

Business logic Service mein.

Database logic Repository mein.

41. modules/ — Business Logic

Ye project ka business layer hai.

modules/
├── auth/
├── hcp/
├── interaction/
└── followup/

Har module ek business domain represent karta hai.

42. Har Module mein 4 Files

Example:

interaction/
├── models.py
├── schemas.py
├── service.py
└── repository.py

In 4 files ko samajh lo, architecture ka 50% clear ho jayega.

43. models.py

Database table ka structure.

For example:

Interaction

contains:

id
hcp_id
user_id
interaction_type
date
time
topics
sentiment
outcomes
follow_up_actions

Ye database side representation hai.

44. schemas.py

API mein input/output ka structure.

Example user sends:

{
    "hcp_id": 10,
    "interaction_type": "Meeting",
    "topics": "Product X efficacy"
}

Pydantic schema validate karega:

Correct type?
Required fields?
Valid values?

So:

Model = Database structure
Schema = API data structure

Dono same cheez nahi hain.

45. service.py

Yahan business logic.

Example:

create_interaction()
update_interaction()
get_interaction()

Suppose interaction create karni hai:

Service
 ↓
Check HCP exists?
 ↓
Check user permission?
 ↓
Validate business rules
 ↓
Repository
46. repository.py

Repository ka kaam:

Database se data lena/dena.

Example:

find_by_id()
create()
update()
search()

Ye database queries handle karega.

So:

Service = What should happen?
Repository = Database mein kaise hoga?
47. auth/
modules/auth/
├── models.py
├── schemas.py
├── service.py
└── repository.py

User authentication/business logic.

48. hcp/
modules/hcp/
├── models.py
├── schemas.py
├── service.py
└── repository.py

HCP related business logic.

49. interaction/
modules/interaction/
├── models.py
├── schemas.py
├── service.py
└── repository.py

Interaction ka complete business logic.

50. followup/
modules/followup/
├── models.py
├── schemas.py
├── service.py
└── repository.py

Follow-up ka complete business logic.

51. integrations/ — External Services
integrations/
├── groq.py
├── storage.py
└── transcription.py

Ye folder external systems ke liye hai.

52. groq.py

Tumhare LLM provider ka integration.

LangGraph
 ↓
LLM Service / Groq Integration
 ↓
Groq API
 ↓
Gemma

Agar future mein LLM provider change karna ho, integration layer isolate hone ki wajah se change easier hota hai.

53. storage.py

Files/audio/images ko object storage mein manage karne ke liye.

For example:

Voice Note
 ↓
Object Storage

PostgreSQL mein generally sirf metadata/reference rakhenge.

54. transcription.py

Voice note ko text mein convert karne ka integration.

Flow:

Voice Note
 ↓
Transcription Service
 ↓
Text
 ↓
LLM
 ↓
Summary

Tumhare screenshot ke:

Summarize from Voice Note

feature ke liye useful.

55. workers/ — Background Jobs
workers/
├── tasks.py
└── queue.py

Har kaam request ke andar immediately karna zaroori nahi.

Example:

Voice Upload
 ↓
Transcription
 ↓
Summary

Agar time lagta hai, background worker use kar sakte ho.

Concept:

FastAPI
 ↓
Queue
 ↓
Worker
 ↓
Task
56. queue.py

Background jobs ko queue/manage karne ke infrastructure ke liye.

Redis-based queue etc. future implementation ho sakta hai.

57. tasks.py

Actual background tasks.

Example:

process_voice_note()
generate_summary()
send_followup_notification()
58. audit/ — Kisne Kya Kiya?

Production CRM mein important.

audit/
├── models.py
├── service.py
└── repository.py

Suppose user ne interaction edit ki:

Interaction #100

Old:
sentiment = Neutral

New:
sentiment = Positive

Audit system record kar sakta hai:

User: 123
Action: EDIT_INTERACTION
Interaction: 100
Old value: Neutral
New value: Positive
Timestamp: ...

Isse system mein accountability aur traceability improve hoti hai.

59. tests/
tests/
├── unit/
├── integration/
└── agent/

Code likhna enough nahi hai.

Production-quality application ko test bhi karna hota hai.

60. Unit Tests
tests/unit/

Individual functions/services test karna.

Example:

search_hcp()
create_interaction()
update_interaction()
61. Integration Tests
tests/integration/

Multiple layers ko saath test karna.

Example:

API
 ↓
Service
 ↓
Repository
 ↓
Database
62. Agent Tests
tests/agent/

Tumhare project mein ye bahut important hai.

Test:

"Find Dr Sharma"

Expected:

search_hcp

Test:

"Show my recent interactions with Dr Sharma."

Expected:

search_hcp
→
interaction_history

Test:

"Create a follow-up for Dr Sharma."

Expected:

follow_up

Isse prove kar sakte ho ki LangGraph actually tools use kar raha hai.

63. .env
.env

Secrets/configuration.

Example:

DATABASE_URL=...
GROQ_API_KEY=...
JWT_SECRET=...
REDIS_URL=...
Important:

.env ko GitHub par upload nahi karna.

64. .env.example

Ye safe template hai:

DATABASE_URL=
GROQ_API_KEY=
JWT_SECRET=
REDIS_URL=

Actual secret nahi.

Developer project clone karke:

.env.example
 ↓
.env

create kar sakta hai.

65. .gitignore

Git ko batata hai:

"In files ko GitHub par mat bhejna."

Example:

.env
__pycache__/
.venv/
.pytest_cache/
66. requirements.txt

Python dependencies.

Tumhare project mein roughly:

FastAPI
Uvicorn
Pydantic
SQLAlchemy
PostgreSQL driver
Alembic
LangGraph
LangChain
Groq client
Pytest

etc.

67. Dockerfile

Docker image banane ke instructions.

Concept:

Dockerfile
 ↓
Docker Image
 ↓
Container
 ↓
FastAPI Application

Isse "mere laptop par chal raha tha" problem reduce hoti hai.

68. docker-compose.yml

Agar multiple services hain:

FastAPI
PostgreSQL
Redis

toh development mein inko ek saath run/manage karne ke liye Docker Compose useful hai.

Concept:

docker-compose
     │
     ├── FastAPI
     ├── PostgreSQL
     └── Redis
69. pyproject.toml

Python project/tool configuration.

Isme project metadata aur tools ki configuration rakh sakte ho.

For example:

pytest
ruff
black

etc.

70. README.md

Ye project ka instruction manual hai.

Isme explain karoge:

What is this project?
Architecture
Features
Tech stack
Installation
Environment variables
How to run
API
AI Agent
6 Tools
Database
Testing
71. Ab poora architecture ek request ke through samjho

Suppose user React mein likhta hai:

"Log a meeting with Dr Sharma. We discussed Product X efficacy and he was positive."

Step 1 — React
React
 ↓
Redux

User message state mein aata hai.

Step 2 — FastAPI
POST /api/v1/chat

Request backend mein aati hai.

Step 3 — Authentication
JWT
 ↓
Current User

System check karta hai user authenticated hai ya nahi.

Step 4 — LangGraph
Chat API
 ↓
HCP Agent
 ↓
State
 ↓
LLM
Step 5 — LLM decides tool

LLM identify karta hai:

search_hcp
Step 6 — Tool
search_hcp
 ↓
HCP Service
 ↓
HCP Repository
 ↓
PostgreSQL

Dr Sharma mil gaya.

Step 7 — Agent

LangGraph state update:

hcp_id = 123

LLM interaction details extract karta hai.

Step 8 — Confirmation

Because database modification ho rahi hai:

Are you sure you want to log this interaction?

User:

Confirm
Step 9 — Log Interaction Tool
log_interaction
 ↓
Interaction Service
 ↓
Permission Check
 ↓
Interaction Repository
 ↓
PostgreSQL
Step 10 — Audit
Audit Service
 ↓
Audit Repository
 ↓
PostgreSQL

Record:

User X logged interaction Y
Step 11 — Response
PostgreSQL
 ↓
Tool
 ↓
LangGraph
 ↓
FastAPI
 ↓
Redux
 ↓
React

UI:

Interaction logged successfully.

72. Architecture ka sabse important concept

Is poore system ko ek sentence mein yaad rakho:

API
 ↓
Agent/Controller
 ↓
Service
 ↓
Repository
 ↓
Database

Aur AI case mein:

API
 ↓
LangGraph
 ↓
Tool
 ↓
Service
 ↓
Repository
 ↓
Database
73. Kaun kya karta hai?

Ye table zaroor yaad rakhna:

Layer	Responsibility
React	UI
Redux	Frontend state
FastAPI API	Requests receive/response send
Middleware	Common request processing
LangGraph	AI workflow/orchestration
LLM	Understand/reason/select tool
Tools	AI ko specific actions provide karna
Service	Business logic
Repository	Database operations
Models	Database structure
Schemas	Request/response validation
PostgreSQL	Persistent data
Redis	Cache/queue/temporary data
Workers	Background processing
Audit	Activity tracking
Tests	Correctness verify karna
Docker	Consistent environment
74. Ek aur simple analogy

Imagine tumhara CRM ek hospital/clinic hai.

React
=
Reception

User yahan se request karta hai.

FastAPI
=
Receptionist

Request ko correct department mein bhejta hai.

LangGraph
=
AI Coordinator

Decide karta hai kya karna hai.

LLM
=
Intelligent Brain

User ki natural language samajhta hai.

Tools
=
Staff ke specialized hands

Har tool specific kaam karta hai.

Services
=
Business Rules / Manager

Decide karta hai action allowed aur valid hai ya nahi.

Repository
=
Database Clerk

Database se data leta/deta hai.

PostgreSQL
=
Records Room

Permanent data store karta hai.

Audit
=
Security Register

Kisne kya kiya record karta hai.

Redis
=
Fast Temporary Desk

Temporary/cache/queue type work.

75. README.md ke liye ready-to-use explanation

Neeche wala section tum directly README mein use kar sakte ho:

Backend Architecture

The backend follows a production-oriented modular monolith architecture using Python and FastAPI. The application is divided into multiple layers so that each part of the system has a clear responsibility.

Architecture Flow
React + Redux
      │
      ▼
   FastAPI
      │
      ├───────────────┐
      │               │
      ▼               ▼
 REST APIs        AI Chat API
      │               │
      │               ▼
      │          LangGraph Agent
      │               │
      │              LLM
      │               │
      │          Tool Selection
      │               │
      │      ┌────────┼─────────┐
      │      ▼        ▼         ▼
      │   Search    Log/Edit   Follow-up
      │    HCP    Interaction
      │      │        │         │
      └──────┴────────┴─────────┘
                     │
                     ▼
                Service Layer
                     │
                     ▼
              Repository Layer
                     │
                     ▼
                PostgreSQL
Project Structure
backend/
│
├── app/
├── tests/
├── alembic/
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── README.md
└── pyproject.toml
app/

Contains the main backend application code.

app/main.py

The entry point of the FastAPI application. It initializes the application, registers routers, middleware, and global exception handlers.

app/core/

Contains application-wide configuration and infrastructure.

config.py — Loads environment variables and application configuration.
security.py — Authentication, JWT and security-related functionality.
logging.py — Application logging configuration.
exceptions.py — Custom application exceptions and error handling.
dependencies.py — Reusable FastAPI dependencies such as database sessions and authenticated users.
app/db/

Contains database infrastructure.

database.py — PostgreSQL connection and database session management.
base.py — SQLAlchemy model base configuration.

Database schema changes are managed using Alembic.

app/api/

Contains the HTTP API layer.

api/
├── router.py
└── v1/
    ├── auth.py
    ├── chat.py
    ├── hcps.py
    ├── interactions.py
    ├── followups.py
    └── users.py

The API layer receives HTTP requests, validates input, authenticates users and calls the appropriate application/service layer.

API versioning is used through /api/v1/ so that future API versions can be introduced without immediately breaking existing clients.

app/agents/

Contains the LangGraph AI agent.

agents/hcp_agent/
├── graph.py
├── state.py
├── nodes.py
├── routing.py
├── prompts.py
└── tool_registry.py
graph.py — Defines the LangGraph workflow.
state.py — Defines the state maintained during an AI interaction.
nodes.py — Contains individual graph processing nodes.
routing.py — Controls transitions between graph nodes.
prompts.py — Contains system prompts and AI instructions.
tool_registry.py — Registers the tools available to the agent.

The LangGraph agent acts as the orchestration layer between the user, LLM and CRM tools.

app/tools/

Contains the six LangGraph tools required by the HCP CRM.

1. Log Interaction
2. Edit Interaction
3. Search HCP
4. Interaction History
5. Follow-up
6. Summarize Interaction

Tools do not directly contain database logic. They call the appropriate service layer, which then communicates with the repository layer.

app/modules/

Contains the core business domains of the application.

modules/
├── auth/
├── hcp/
├── interaction/
└── followup/

Each domain contains:

models.py
schemas.py
service.py
repository.py

Models represent database entities.

Schemas define and validate API input/output using Pydantic.

Services contain business logic and application rules.

Repositories handle database operations.

This separation keeps the application maintainable and testable.

app/integrations/

Contains integrations with external systems.

groq.py — Groq LLM integration.
storage.py — File/object storage integration.
transcription.py — Voice-to-text integration.

External services are isolated from the core business logic so they can be changed more easily in the future.

app/workers/

Contains background processing.

Examples include:

Voice-note processing
Transcription
AI summarization
Follow-up notifications

Long-running operations can be moved to background workers instead of blocking API requests.

app/audit/

Contains audit logging functionality.

The audit system records important actions such as:

Who performed the action?
What action was performed?
Which record was affected?
When did it happen?
What changed?

This provides traceability for CRM operations.

tests/

Contains automated tests.

tests/
├── unit/
├── integration/
└── agent/
Unit tests test individual functions/services.
Integration tests test API, service, repository and database interactions.
Agent tests verify LangGraph routing and correct tool selection.
alembic/

Alembic manages database schema migrations.

For example:

Migration 001 → Create HCP table
Migration 002 → Create Interaction table
Migration 003 → Add Follow-up table

This allows database schema changes to be tracked and reproduced across environments.

.env

Contains environment-specific secrets and configuration such as:

DATABASE_URL
GROQ_API_KEY
JWT_SECRET
REDIS_URL

The .env file must not be committed to GitHub.

.env.example

Provides a template showing which environment variables are required without exposing real secrets.

requirements.txt

Contains the Python dependencies required to run the backend.

Dockerfile

Defines how the backend application is packaged into a Docker image.

docker-compose.yml

Used to run multiple development services together, such as:

FastAPI
PostgreSQL
Redis
pyproject.toml

Contains Python project configuration and development-tool configuration.

76. Ek important correction jo main abhi karunga

Tumhare original structure mein:

app/db/migrations/

aur

alembic/

dono hain.

Main ise final project mein aise rakhunga:

backend/
│
├── app/
│   ├── main.py
│   ├── core/
│   ├── db/
│   │   ├── database.py
│   │   └── base.py
│   ├── api/
│   ├── agents/
│   ├── tools/
│   ├── modules/
│   ├── integrations/
│   ├── workers/
│   └── audit/
│
├── alembic/
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
│
├── tests/
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── README.md
└── pyproject.toml

Ye cleaner hai.

Aur ek aur principle yaad rakh:

                 LANGGRAPH
                     │
                     ▼
                   TOOL
                     │
                     ▼
                  SERVICE
                     │
                     ▼
                REPOSITORY
                     │
                     ▼
                POSTGRESQL

LLM → Database direct nahi.

Tool → Database direct nahi.

Ye separation tumhare project ko genuinely maintainable banata hai.

Agar tum is architecture ko implement karoge, toh best development order hoga:

1. Database design
        ↓
2. Models
        ↓
3. Schemas
        ↓
4. Repositories
        ↓
5. Services
        ↓
6. FastAPI APIs
        ↓
7. 6 Tools
        ↓
8. LangGraph State
        ↓
9. LangGraph Graph
        ↓
10. Groq + Gemma
        ↓
11. React + Redux integration
        ↓
12. Auth/RBAC
        ↓
13. Audit
        ↓
14. Tests
        ↓
15. Docker/Deployment

Isi order mein karna, warna beginner ke liye sab kuch ek saath mix ho jayega.


# Recommended Frontend Structure


frontend/
│
├── src/
│   │
│   ├── app/
│   │   ├── store.js
│   │   ├── rootReducer.js
│   │   └── router.jsx
│   │
│   ├── assets/
│   │   ├── images/
│   │   └── icons/
│   │
│   ├── components/
│   │   ├── common/
│   │   │   ├── Button.jsx
│   │   │   ├── Input.jsx
│   │   │   ├── Modal.jsx
│   │   │   ├── Loader.jsx
│   │   │   └── ErrorMessage.jsx
│   │   │
│   │   ├── layout/
│   │   │   ├── Navbar.jsx
│   │   │   ├── Sidebar.jsx
│   │   │   └── MainLayout.jsx
│   │   │
│   │   └── chat/
│   │       ├── ChatWindow.jsx
│   │       ├── ChatMessage.jsx
│   │       ├── ChatInput.jsx
│   │       └── ToolResult.jsx
│   │
│   ├── features/
│   │   │
│   │   ├── auth/
│   │   │   ├── authSlice.js
│   │   │   ├── authApi.js
│   │   │   └── Login.jsx
│   │   │
│   │   ├── hcp/
│   │   │   ├── hcpSlice.js
│   │   │   ├── hcpApi.js
│   │   │   ├── HCPList.jsx
│   │   │   ├── HCPSearch.jsx
│   │   │   └── HCPProfile.jsx
│   │   │
│   │   ├── interactions/
│   │   │   ├── interactionSlice.js
│   │   │   ├── interactionApi.js
│   │   │   ├── InteractionList.jsx
│   │   │   ├── InteractionForm.jsx
│   │   │   ├── InteractionDetails.jsx
│   │   │   └── InteractionHistory.jsx
│   │   │
│   │   ├── followups/
│   │   │   ├── followupSlice.js
│   │   │   ├── followupApi.js
│   │   │   ├── FollowupList.jsx
│   │   │   └── FollowupForm.jsx
│   │   │
│   │   └── ai/
│   │       ├── aiSlice.js
│   │       ├── aiApi.js
│   │       └── AIChat.jsx
│   │
│   ├── pages/
│   │   ├── LoginPage.jsx
│   │   ├── DashboardPage.jsx
│   │   ├── HCPPage.jsx
│   │   ├── InteractionPage.jsx
│   │   └── NotFoundPage.jsx
│   │
│   ├── services/
│   │   ├── apiClient.js
│   │   └── endpoints.js
│   │
│   ├── hooks/
│   │   ├── useAuth.js
│   │   └── useDebounce.js
│   │
│   ├── utils/
│   │   ├── formatDate.js
│   │   ├── validators.js
│   │   └── constants.js
│   │
│   ├── styles/
│   │   ├── globals.css
│   │   └── variables.css
│   │
│   ├── App.jsx
│   └── main.jsx
│
├── public/
│
├── .env
├── .env.example
├── .gitignore
├── package.json
├── vite.config.js
└── README.md
2. Pehle Big Picture Samajh

Tumhara complete system:

                    FRONTEND
               React + Redux
                      │
                      │ HTTP
                      ▼
                 FASTAPI
                      │
          ┌───────────┴───────────┐
          │                       │
       REST APIs             AI Chat API
          │                       │
          │                  LangGraph
          │                       │
          │                      LLM
          │                       │
          │                     Tools
          │                       │
          └───────────┬───────────┘
                      │
                  Services
                      │
                 Repository
                      │
                  PostgreSQL

Frontend ka kaam primarily:

User ko interface dena + user actions ko backend APIs tak pahunchana + response ko UI mein dikhana.

3. src/
src/

Ye frontend application ka main code hai.

Backend mein tumhare paas:

backend/app/

tha.

Frontend mein:

frontend/src/

actual application code rakhega.

4. main.jsx
src/main.jsx

Ye frontend ka entry point hai.

Conceptually:

Browser
   ↓
main.jsx
   ↓
React Application
   ↓
App.jsx

Yahin se React application start hoti hai.

5. App.jsx
src/App.jsx

Ye application ka main component/container hai.

For example:

App
 │
 ├── Login
 │
 ├── Dashboard
 │
 ├── HCP
 │
 └── Interactions

Lekin actual routing hum router.jsx mein rakhenge.

6. app/ — Redux + Application Configuration
src/app/
├── store.js
├── rootReducer.js
└── router.jsx

Ye frontend ka application-level configuration hai.

store.js

Tumhari requirement mein Redux hai.

Redux ka simple meaning:

Application ka centralized state store.

Example:

Redux Store
│
├── auth
├── hcp
├── interactions
├── followups
└── ai

Suppose current HCP:

Dr. Sharma

selected hai.

Ya AI conversation:

User: Log meeting with Dr Sharma
AI: Sure...

Toh relevant state Redux mein maintain ki ja sakti hai.

7. rootReducer.js

Different Redux slices ko combine karega:

authSlice
hcpSlice
interactionSlice
followupSlice
aiSlice
       ↓
rootReducer
       ↓
Redux Store
8. router.jsx

Frontend ke pages/routes define karega.

Example:

/login
/dashboard
/hcps
/hcps/:id
/interactions
/interactions/:id

So:

URL
 ↓
React Router
 ↓
Correct Page
9. components/

Ye reusable UI components hain.

components/
├── common/
├── layout/
└── chat/
10. components/common/

Generic components.

Example:

Button.jsx
Input.jsx
Modal.jsx
Loader.jsx
ErrorMessage.jsx

Suppose tumhe 20 jagah button chahiye.

Instead of 20 baar button ka same code:

Button.jsx

banake reuse karoge.

<Button>
Save Interaction
</Button>
11. components/layout/

Application ka common layout.

Navbar
Sidebar
MainLayout

Tumhara CRM roughly:

┌─────────────────────────────────────┐
│              Navbar                 │
├──────────┬──────────────────────────┤
│          │                          │
│ Sidebar  │       Main Content       │
│          │                          │
│ Dashboard│                          │
│ HCPs     │                          │
│ Interact.│                          │
│ Followup │                          │
│ AI       │                          │
│          │                          │
└──────────┴──────────────────────────┘
12. components/chat/

Ye tumhare AI conversational interface ke liye hai.

Requirement mein specifically:

Structured Form OR Conversational Chat

hai.

Isliye:

chat/
├── ChatWindow.jsx
├── ChatMessage.jsx
├── ChatInput.jsx
└── ToolResult.jsx
ChatWindow.jsx

Complete chat area.

┌──────────────────────────────┐
│ AI HCP Assistant             │
├──────────────────────────────┤
│ User: Find Dr Sharma         │
│                              │
│ AI: I found Dr Sharma.       │
│                              │
│ User: Log today's meeting    │
│                              │
├──────────────────────────────┤
│ Type message...       [Send] │
└──────────────────────────────┘
ChatMessage.jsx

Individual message.

User message
AI message

ko display karega.

ChatInput.jsx

User ka message input.

ToolResult.jsx

AI ne agar tool execute kiya:

search_hcp

toh UI mein result dikha sakta hai.

Example:

✓ HCP Found

Dr. Sharma
Cardiologist
Delhi
13. features/ — Sabse Important Frontend Folder

Ab important concept.

Tumhare frontend mein feature-based architecture use karenge.

features/
├── auth/
├── hcp/
├── interactions/
├── followups/
└── ai/

Matlab:

Ek business feature se related UI + Redux + API code ek jagah.

Ye large projects mein kaafi clean approach hoti hai.

14. features/auth/
auth/
├── authSlice.js
├── authApi.js
└── Login.jsx

Authentication related frontend code.

authSlice.js

Redux state:

user
token
isAuthenticated
loading
error
authApi.js

Backend se login call.

POST /api/v1/auth/login
Login.jsx

Login screen.

15. features/hcp/
hcp/
├── hcpSlice.js
├── hcpApi.js
├── HCPList.jsx
├── HCPSearch.jsx
└── HCPProfile.jsx

HCP-related functionality.

HCPSearch.jsx

User:

Search Dr Sharma

Backend:

GET /api/v1/hcps?search=Sharma
HCPProfile.jsx

HCP details:

Dr. Sharma
Speciality
Hospital
Location
Recent Interactions
Follow-ups
16. features/interactions/

Tumhare project ka core frontend feature.

interactions/
├── interactionSlice.js
├── interactionApi.js
├── InteractionList.jsx
├── InteractionForm.jsx
├── InteractionDetails.jsx
└── InteractionHistory.jsx
17. InteractionForm.jsx

Ye tumhari structured Log Interaction Screen hai.

Something like:

┌─────────────────────────────────────┐
│ Log Interaction                     │
├─────────────────────────────────────┤
│ HCP                                 │
│ [ Dr. Sharma                    ]   │
│                                     │
│ Interaction Type                    │
│ [ Face-to-Face ▼ ]                  │
│                                     │
│ Date                                │
│ [ 04 Sep 2026 ]                     │
│                                     │
│ Topics Discussed                    │
│ [ Product X efficacy             ]  │
│                                     │
│ HCP Sentiment                       │
│ [ Positive ▼ ]                      │
│                                     │
│ Outcome                             │
│ [ Interested in Product X        ]  │
│                                     │
│ Follow-up Required                  │
│ [ ✓ ]                               │
│                                     │
│          [Cancel] [Save Interaction]│
└─────────────────────────────────────┘
18. InteractionHistory.jsx

HCP ki interaction history:

Dr. Sharma

04 Sep
Meeting
Product X
Positive

28 Aug
Call
Product Y
Neutral

20 Aug
Email
Product X
Positive
19. interactionSlice.js

Redux interaction state.

Example:

interactions
selectedInteraction
loading
error
20. interactionApi.js

Backend interaction APIs ko call karega.

For example:

POST /api/v1/interactions
GET /api/v1/interactions
GET /api/v1/interactions/:id
PUT /api/v1/interactions/:id
21. features/followups/
followups/
├── followupSlice.js
├── followupApi.js
├── FollowupList.jsx
└── FollowupForm.jsx

Follow-up management.

Example:

Follow-up with Dr Sharma

Date: 10 Sep
Purpose: Product X discussion
Status: Pending
22. features/ai/
ai/
├── aiSlice.js
├── aiApi.js
└── AIChat.jsx

Ye LangGraph backend se communicate karega.

aiApi.js

Example:

POST /api/v1/chat

Request:

{
  "message": "Find Dr Sharma"
}

Backend:

FastAPI
 ↓
LangGraph
 ↓
LLM
 ↓
Search HCP Tool

Response:

{
  "message": "I found Dr Sharma.",
  "tool": "search_hcp"
}

Frontend usko display karega.

23. pages/
pages/
├── LoginPage.jsx
├── DashboardPage.jsx
├── HCPPage.jsx
├── InteractionPage.jsx
└── NotFoundPage.jsx

Pages ko tum complete screens samjho.

Difference:

components = small reusable pieces

pages = complete screens

Example:

InteractionPage
     │
     ├── InteractionForm
     ├── HCP selector
     ├── InteractionHistory
     └── AIChat
24. services/
services/
├── apiClient.js
└── endpoints.js

Backend communication ka common setup.

apiClient.js

Central HTTP client.

Example:

React
 ↓
apiClient
 ↓
FastAPI

Yahan:

Base URL
Headers
JWT token
Error handling

centralize kiya ja sakta hai.

25. endpoints.js

API endpoints ko centralize kar sakte ho.

Example:

AUTH_LOGIN
HCP_SEARCH
INTERACTION_CREATE
INTERACTION_UPDATE
CHAT
FOLLOWUP_CREATE

Isse URL strings poore project mein scattered nahi rahenge.

26. hooks/
hooks/
├── useAuth.js
└── useDebounce.js

Reusable React logic.

useAuth.js

Current user/authentication information access karne mein help.

useDebounce.js

HCP search mein useful.

User:

D
Dr
Dr S
Dr Sh
Dr Sha

har keystroke par API call karne ke bajaye thoda wait karke search karwa sakte ho.

27. utils/

Small helper functions.

utils/
├── formatDate.js
├── validators.js
└── constants.js

Example:

2026-09-04

ko:

04 Sep 2026

display karna.

28. styles/
styles/
├── globals.css
└── variables.css

Global styling.

Tumhari requirement:

Google Inter font

hai.

Toh global styling mein Inter configure kar sakte ho.

29. Final Frontend + Backend Architecture

Ab dono ko combine karo:

CRM/
│
├── frontend/
│   │
│   ├── src/
│   │   ├── app/
│   │   ├── assets/
│   │   ├── components/
│   │   ├── features/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── hooks/
│   │   ├── utils/
│   │   ├── styles/
│   │   ├── App.jsx
│   │   └── main.jsx
│   │
│   ├── public/
│   ├── package.json
│   ├── vite.config.js
│   └── README.md
│
└── backend/
    │
    ├── app/
    │   ├── main.py
    │   ├── core/
    │   ├── db/
    │   ├── api/
    │   ├── agents/
    │   ├── tools/
    │   ├── modules/
    │   ├── integrations/
    │   ├── workers/
    │   └── audit/
    │
    ├── tests/
    ├── alembic/
    ├── requirements.txt
    ├── Dockerfile
    ├── docker-compose.yml
    └── README.md
30. Sabse Important — Tumhare Log Interaction Screen ka Architecture

Tumhara assignment specifically Log Interaction Screen ke around hai.

Isliye iska flow tumhe clearly samajhna chahiye:

                 LOG INTERACTION
                       │
             ┌─────────┴─────────┐
             │                   │
             ▼                   ▼
      Structured Form       AI Chat
             │                   │
             │                   ▼
             │               FastAPI
             │                   │
             │               LangGraph
             │                   │
             │                  LLM
             │                   │
             │            log_interaction
             │                   │
             └─────────┬─────────┘
                       ▼
                Interaction
                   Service
                       │
                 Repository
                       │
                   PostgreSQL

Yaani same backend business logic dono interfaces se use ho sakti hai.

Ye tumhare project ka ek strong architectural point hai.

31. Structured Form vs AI Chat
Structured Form
User
 ↓
InteractionForm.jsx
 ↓
Redux/API
 ↓
FastAPI
 ↓
Interaction Service
 ↓
PostgreSQL
Conversational
User
 ↓
AIChat.jsx
 ↓
FastAPI /chat
 ↓
LangGraph
 ↓
Groq/Gemma
 ↓
log_interaction Tool
 ↓
Interaction Service
 ↓
PostgreSQL

Dono ka final destination same business/service layer hai.

Ye design tum video mein explain kar sakte ho.

32. Tumhare 6 Tools ka Frontend se Relation
Tool	Frontend
Log Interaction	InteractionForm.jsx + AI Chat
Edit Interaction	InteractionDetails.jsx + AI Chat
Search HCP	HCPSearch.jsx + AI Chat
Interaction History	InteractionHistory.jsx + AI Chat
Follow-up	FollowupForm.jsx + AI Chat
Summarize Interaction	AIChat.jsx / Interaction Details

Important:

Tool ka frontend mein hona compulsory nahi hai.

Tool backend LangGraph ka component hai.

Frontend sirf user interface provide karta hai.

33. Ek Line Mein Pura Project

Isko yaad kar lo:

React
→ Redux
→ FastAPI
→ LangGraph
→ Groq LLM
→ Tools
→ Services
→ Repositories
→ PostgreSQL

Aur normal structured form ke case mein:

React
→ Redux
→ FastAPI
→ Services
→ Repositories
→ PostgreSQL

AI-first part sirf chat nahi hai — LangGraph agent + LLM + tools actual intelligence/orchestration layer hai.