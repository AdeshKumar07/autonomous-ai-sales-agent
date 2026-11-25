# Technology Stack

## Frontend

- **React.js**: Component-based UI library for building the CRM dashboard and voice interaction interface.
- **Vite**: Fast frontend build tool and development server.
- **JavaScript**: Core frontend programming language.
- **Tailwind CSS**: Utility-first CSS framework integrated via `@tailwindcss/vite`.
- **Axios**: Promise-based HTTP client for communicating with the FastAPI backend.
- **React Router DOM**: Client-side routing for navigating dashboard views.
- **Lucide React**: Icon library for UI controls and status indicators.
- **Recharts**: Charting library for CRM analytics and lead metrics.
- **Browser Web Speech API**: Planned for client-side speech recognition and synthesis.

## Backend

- **Python 3.11**: Core backend runtime.
- **FastAPI**: Modern, async-ready web framework for building REST APIs.
- **Uvicorn**: ASGI server for running FastAPI.
- **Pydantic**: Data validation and settings/schema serialization.
- **SQLAlchemy**: ORM and SQL toolkit for database operations.
- **psycopg2-binary**: PostgreSQL database adapter for Python.
- **python-dotenv**: Environment variable loading from `.env` files.
- **OpenAI Python SDK**: Integration with OpenAI models.

## Database & AI / RAG

- **PostgreSQL 18.1**: Relational database for leads, customers, appointments, and CRM records.
- **ChromaDB**: Vector database for storing and querying document embeddings in the RAG pipeline.
