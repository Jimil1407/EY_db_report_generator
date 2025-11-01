# AI Report Generator

## Software Requirements Specification (SRS)

## 1. Introduction

### 1.1 Purpose  
This document specifies the requirements for the AI-powered Medical Claims Analytics Bot that enables executives to query a large Oracle medical claims database using natural language and receive accurate, audited PDF reports.

### 1.2 Intended Audience  
- Developers implementing the system  
- Project Managers overseeing delivery  
- QA teams verifying functionality  
- Security & Compliance officers reviewing access controls  
- Stakeholders and decision-makers evaluating progress

### 1.3 Scope  
The software translates natural language queries to SQL, runs them read-only on Oracle DB, validates query safety, and generates PDF reports with audit trails. It uses FastAPI backend, Google Gemini AI for NL-to-SQL, and ReportLab for PDF generation.

### 1.4 Glossary  
- **Gemini API:** Large language model service converting NL to SQL.  
- **FastAPI:** Python web framework for async backend.  
- **Read-only User:** Oracle DB user with only SELECT privileges.  
- **Audit Trail:** Logs of queries and user metadata for compliance.

### 1.5 Flow diagram

┌─────────────────────────────────────────────────────────────┐
│                     Executive/UI Layer                       │
│                  (Web Browser, API Client)                  │
└────────────────────────────┬────────────────────────────────┘
                             ↓
        ┌────────────────────────────────────────┐
        │      FastAPI Backend                   │
        │  ├─ Query Routing                      │
        │  ├─ Request Validation (Pydantic)      │
        │  └─ Response Formatting                │
        └──┬──────────────────────────────────┬──┘
                              |                
    ┌────────────────────┐    |     ┌──────────────────┐
    │   Gemini API       │    |     │  SQL Validator   │
    │   (NL → SQL)       │    |     │  (Safety Checks) │
    │                    │    |     │  - No INSERT     │
    │ Rate: 15 RPM       │    |     │  - No DELETE     │
    │ Free Tier          │    |     │  - No DROP       │
    └────────────────────┘    |     └──────────────────┘
           ^                  |
           |                  V
    ┌────────────────────────────────────────┐
    │   Schema Manager + Schema Selector     │
    │   ├─ Cache (in-memory)                 │
    │   ├─ Semantic retrieval                │
    │   └─ Only send relevant tables to LLM  │
    └────────────────────────────────────────┘
           ↓
    ┌────────────────────────────────────────┐
    │   Oracle Database Layer                │
    │   ├─ Connection Pool (5-20 conns)      │
    │   ├─ Query Execution                   │
    │   └─ Result Fetching                   │
    └────────────────────────────────────────┘
           ↓
    ┌────────────────────────────────────────┐
    │   Report Generation                    │
    │   ├─ ReportLab (PDF creation)          │
    │   ├─ Format results                    │
    │   └─ Add metadata (query, timestamp)   │
    └────────────────────────────────────────┘
           ↓
    ┌────────────────────────────────────────┐
    │   PDF + Audit Trail to Executive       │
    └────────────────────────────────────────┘



## 2. Overall Description

### 2.1 Product Perspective  
Standalone microservice backend integrated with Oracle DB and AI model APIs providing REST API endpoints to internal web apps and third-party clients.

### 2.2 Product Functions  
- Accept natural language query inputs  
- Generate Oracle-compliant SELECT-only SQL queries using Gemini AI  
- Validate queries for syntax and safety  
- Execute queries on Oracle using read-only credentials  
- Format and generate PDF reports of query results  
- Store and securely deliver PDF reports  
- Maintain comprehensive audit logs for compliance

### 2.3 User Classes and Characteristics  
- Executives: Submit queries via simple interfaces  
- Analysts: Monitor accuracy and audit logs  
- Admins: Manage system configuration and API keys

### 2.4 Operating Environment  
- Python 3.10+ server with FastAPI  
- Oracle DB 19c+ accessible via network  
- Secure internet connection to Gemini API  

## 3. System Features and Requirements

### 3.1 Functional Requirements

#### 3.1.1 Query Processing  
- Accept NL queries over REST API  
- Generate only SELECT SQL queries  
- Reject queries with modification keywords  
- Use read-only Oracle DB connection for execution

#### 3.1.2 PDF Reporting  
- Generate detailed PDF reports with metadata  
- Include data tables, charts, and audit info  
- Ensure reports adhere to government confidentiality policies

#### 3.1.3 Audit Logging  
- Log user ID, timestamp, query, SQL, and execution metadata  
- Store immutable logs with at least 7 years retention

### 3.2 Non-Functional Requirements

#### 3.2.1 Performance  
- 95% queries respond within 5 seconds  
- Support at least 50 concurrent users

#### 3.2.2 Security  
- Enforce read-only permissions at DB and application layers  
- Require API key authentication and role-based access  
- Encrypt all data at rest and in transit

#### 3.2.3 Reliability  
- 99.5% uptime with monitored health checks  
- Retry mechanism for retrying query generation up to 3 times

#### 3.2.4 Usability  
- Provide Swagger/OpenAPI docs for API  
- Easy-to-use REST endpoints

## 4. External Interface Requirements

- REST API endpoints for query submission, schema retrieval, and health checks  
- Oracle DB connectivity using python-oracledb  
- Gemini API access over HTTPS  
- PDF storage via local filesystem or cloud storage like S3

## 5. Other Requirements

- Comply with Government of Telangana data and audit regulations  
- Paginate or limit very large query results  
- Provide manual schema refresh endpoint for admins  

---

This Markdown SRS can be added verbatim into your README file or repository docs folder to communicate project requirements clearly to all stakeholders.
