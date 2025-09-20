# Video-Analysis-Service
Video analysis service for detecting non ergonomic hand postures

## Requirements

* [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows/Mac) or Docker Engine (Linux).
* `.env` file with environment variables.
* Deployed Kafka broker, MongoDB, and MySQL.

##  Project structure 📁

```bash
📁 VIDEO-ANALYSIS-SERVICE/              # Root directory of the service
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
│   │   ├── 📁 video/                   # Video analysis related
│   │   │   ├── analyzer.py             # Main algorith to analyze video
│   │   │   ├── 📁 detection/           # Detection of valid frames
│   │   │   ├── 📁 models/              # YOLO and Mediapipe models management
│   │   │   ├── 📁 rules/               # Main error detection and tracking
│   │   │   └── 📁 utils/               # Utils
│   │   └── 📁 repositories/            # Concrete repository implementations
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

Edit the .example.env file with actual variables, and rename it to .env


### Run the service

```bash
docker compose up --build -d
```

### Check running containers in Docker Desktop / Docker Engine

```bash
docker ps
```

### Test the service

Developing unit tests

### Stop the service

```bash
docker compose down
```