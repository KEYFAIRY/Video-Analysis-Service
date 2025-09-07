# Video-Analysis-Service
Video analysis service for detecting non ergonomic hand postures

## Requirements

* [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows/Mac) or Docker Engine (Linux).
* `.env` file with environment variables.
* Deployed Kafka broker, MongoDB, and MySQL.

##  Project structure 📁

```bash
📁 VIDEO-ANALYSIS-SERVICE/              # Root directory of the worker service
│
├── 📁 app/                             # Main application code
│   ├── main.py                         # Entry point: starts Kafka consumer + FastAPI app
│   │
│   ├── 📁 core/                        # Core configurations
│   │   ├── config.py                   # Environment variables (Kafka, DBs, storage path)
│   │   ├── logging.py                  # Logging configuration
│   │   └── exceptions.py               # Custom exception definitions
│   │
│   ├── 📁 domain/                      # Business logic (independent of tech)
│   │   ├── 📁 entities/                # Core entities ()
│   │   ├── 📁 repositories/            # Repository interfaces ()
│   │   └── 📁 services/                # Domain services ()
│   │
│   ├── 📁 application/                 # Application layer (use case orchestration)
│   │   ├── 📁 use_cases/               # Use cases ()
│   │   ├── 📁 dto/                     # Data Transfer Objects
│   │
│   ├── 📁 infrastructure/              # Technical implementations
│   │   ├── 📁 kafka/                   # Kafka consumer and producer
│   │   ├── 📁 database/                # Database adapters
│   │   │   └── 📁 models/              # Database models
│   │   ├── 📁 storage/                 # Local file system access (read videos)
│   │   └── 📁 repositories/            # Concrete repository implementations
│   │
│   ├── 📁 presentation/               # Presentation layer (API and external interfaces)
│   │   ├── 📁 api/                    # REST API endpoints
│   │   │   └── 📁 v1/                 # API v1 endpoints
│   │   │       └── dependencies.py    # Shared dependencies (DI)
│   │   ├── 📁 schemas/                # Pydantic schemas ()
│   │   └── 📁 middleware/             # Custom middleware (CORS, logging, error handling)
│   │
│   └── 📁 shared/                      # Shared utilities
│       ├── constants.py                # Global constants
│       ├── enums.py                    # Enumerations
│       └── utils.py                    # Helper functions
│
├── 📁 tests/                           # Unit tests
│   ├── 📁 domain/
│   ├── 📁 application/
│   └── 📁 infrastructure/
│
├── 📁 scripts/                         # Helper scripts
│   └── start.sh                        # Script to start the service
│
├── .env                                # Environment variables (not committed to Git)
├── Dockerfile                          # Instructions to build Docker image
├── docker-compose.yml                  # Runs only this service container
├── requirements.txt                    # Python dependencies
└── README.md                           # Project documentation

```


## Steps to run the project

### Create .env file, for example:

Edit the .example.env file with yout actual variables, and rename it to .env


### Run the service

```bash
docker compose up --build -d
```

### Check running containers in Docker Desktop / Docker Engine

```bash
docker ps
```

### Test the service

Developing kafdrop to manually test kafka functionalities, but the endpoints are accesible [Here](http://localhost:8100).

### Stop the service

```bash
docker compose down
```