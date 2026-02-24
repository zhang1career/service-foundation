# Service Foundation

A Django-based service foundation project providing reusable microservices and common utilities.

## Overview

This project serves as a foundation for building scalable web services, offering a collection of reusable applications and shared components. It is built with Django 4.1 and follows best practices for modular architecture.

## Applications

### [app_oss](./app_oss/README.md) - Object Storage Service

A local object storage service that provides AWS S3-compatible REST API endpoints. It stores objects on the local filesystem while maintaining full compatibility with S3 operations, making it ideal for development, testing, and scenarios where cloud storage is not required.

**Key Features:**
- Local filesystem storage with configurable base path
- Full S3 API compatibility (PUT, GET, DELETE, HEAD, ListObjectsV2)
- Object copying with metadata directives
- Custom metadata support via `x-amz-meta-*` headers
- Pagination support for object listing
- Unified view routing for all S3 operations

**API Endpoint:** `/api/oss/`

For detailed documentation, see [app_oss/README.md](./app_oss/README.md).

### app_snowflake - Snowflake ID Generator

A distributed unique ID generator service based on the Snowflake algorithm. Provides high-performance ID generation for distributed systems.

**API Endpoint:** `/api/snowflake/`

## Common Module

The `common` module provides shared utilities, services, and components used across applications:

- **Utils**: Environment variable management, date/time helpers, text processing, etc.
- **Services**: AI services, multimedia processing, email services, storage services
- **Components**: Singleton pattern, middleware, exception handling
- **Drivers**: Database and service drivers (MongoDB, Milvus, Neo4j)
- **Constants**: Application-wide constants and enums

## Getting Started

### Prerequisites

- Python 3.8+
- Django 4.1+
- See `requirements.txt` for full dependencies

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Build frontend assets (Tailwind CSS + Neo4j NVL):
   ```bash
   npm install && npm run build
   ```
4. Configure environment variables in `.env` file
5. Run migrations:
   ```bash
   python manage.py migrate
   ```
6. Start the development server:
   ```bash
   python manage.py runserver
   ```

### Configuration

Create a `.env` file in the project root with required configuration. See individual application READMEs for specific configuration requirements.

## Project Structure

```
service_foundation/
├── app_oss/              # Object Storage Service
├── app_snowflake/        # Snowflake ID Generator
├── common/               # Shared utilities and components
├── service_foundation/   # Django project settings
├── manage.py
└── requirements.txt
```

## License

See [LICENSE](./LICENSE) for details.

