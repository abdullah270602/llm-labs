# LLM LABS

LLM LABS is a robust, scalable backend API built with FastAPI and PostgreSQL, designed to power collaborative AI-driven chat and workspace applications. It supports user authentication (Google OAuth), chat conversations with LLMs (OpenAI, Groq, DeepSeek), workspace and folder management, and flexible movement of chats and folders. The backend is modular, secure, and ready for production deployment.

---

## Features

- **User Authentication**
  - Google OAuth 2.0 login
  - JWT-based session management

- **Chat System**
  - Create and manage chat conversations with LLMs
  - Supports multiple AI model providers (OpenAI, Groq, DeepSeek)
  - Automatic chat title generation using LLMs
  - Model switching per conversation

- **Workspace & Folder Management**
  - Organize chats into workspaces and folders
  - Move chats and folders between global, workspace, and folder scopes
  - Soft and permanent deletion modes for workspaces and folders

- **API Design**
  - RESTful endpoints with FastAPI
  - Modular route structure: `/api/chats`, `/api/models`, `/api/workspaces`, `/api/folders`, `/api/move`, `/auth`
  - CORS and session middleware for secure frontend integration

- **Database**
  - PostgreSQL with psycopg2
  - Context-managed connections for reliability
  - Efficient queries for workspace, folder, and chat retrieval

- **Extensibility**
  - Easily add new LLM providers or prompt templates
  - Clear separation of concerns for services, routes, and database logic

---

## Getting Started

### Prerequisites

- Python 3.10+
- PostgreSQL database
- [pip](https://pip.pypa.io/en/stable/)

### Environment Variables

Create a `.env` file in the `root/` directory with the following keys:

```
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=your_db_name
BRANCH_DB_HOST=your_db_host
DB_PORT=5432
SESSION_SECRET_KEY=your_session_secret
JWT_SECRET_KEY=your_jwt_secret
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
OPENAI_API_KEY=your_openai_key
GROQ_API_KEY=your_groq_key
DEEPSEEK_API_KEY=your_deepseek_key
```

### Installation

1. **Clone the repository**
   ```sh
   git clone https://github.com/abdullah270602/llm-labs.git
   cd llm-labs
   ```

2. **Install dependencies**
   ```sh
   pip install -r requirements.txt
   ```

3. **Set up the database**
   - Create the PostgreSQL database and run the necessary migrations or SQL scripts to create tables (`users`, `workspaces`, `folders`, `conversations`, `messages`, `models`, etc.).

4. **Run the server**
   ```sh
   uvicorn main:app --reload
   ```

   The API will be available at `http://localhost:8000`.

---

## API Overview

- **Authentication:**  
  - `/google/login` – Start Google OAuth login  
  - `/auth/callback` – OAuth callback, returns JWT

- **Chats:**  
  - `POST /api/chats/` – Create a new chat  
  - `POST /api/chats/message/` – Add a message to a chat  
  - `GET /api/chats/{chat_id}/` – Get chat by ID  
  - `PUT /api/chats/title/{chat_id}` – Update chat title  
  - `DELETE /api/chats/{chat_id}/` – Delete chat

- **Models:**  
  - `GET /api/models/` – List available LLM models

- **Workspaces:**  
  - `POST /api/workspaces/` – Create workspace  
  - `GET /api/workspaces/user/{user_id}` – List user workspaces  
  - `DELETE /api/workspaces/{workspace_id}` – Delete workspace  
  - `GET /api/workspaces/{workspace_id}/chats` – List chats in workspace  
  - `GET /api/workspaces/{workspace_id}/folders` – List folders in workspace

- **Folders:**  
  - `POST /api/folders/` – Create folder  
  - `DELETE /api/folders/{folder_id}` – Delete folder  
  - `GET /api/folders/global/{user_id}` – List user's global folders

- **Movement:**  
  - `POST /api/move/` – Move chat or folder between locations

---

## Contributing

1. Fork the repo and create your branch.
2. Make your changes and add tests.
3. Submit a pull request.

---

