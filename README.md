# ESPAgent

ESP-IDF MCP agent for ESP32 development tasks.

## Features

- **LLM-powered agent** using ChatOpenAI (GLM-4.6)
- **MCP (Model Context Protocol)** tool integration
- **Cross-session memory** with PostgreSQL backend
- **Human-in-the-loop** approval for sensitive operations
- **SSH remote execution** capabilities
- **Modular middleware system** for extensibility

## Requirements

- Python 3.10+
- PostgreSQL database
- MCP server (for tool integration)

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd espagent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

## Configuration

Create a `.env` file in the project root:

```bash
# Database configuration
DATABASE_URL=postgresql://user:password@localhost:5432/espagent

# API configuration
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE=https://open.bigmodel.cn/api/coding/paas/v4
```

## Usage

### Command Line Interface

```bash
espagent
```

### Python Module

```bash
python -m espagent
```

## Project Structure

```
espagent/
├── agent.py          # Agent initialization
├── cli.py            # CLI interface
├── middlewares.py    # Middleware configurations
├── models.py         # LLM model definitions
├── tools/            # Tool implementations
│   ├── mcp.py        # MCP integration
│   ├── memory.py     # Memory tools
│   └── ssh.py        # SSH tool
└── utils/            # Utilities
    ├── human_in_the_loop.py
    └── state.py
```

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run linting
ruff check .

# Format code
ruff format .

# Run tests
pytest

# Run tests with coverage
pytest --cov=espagent --cov-report=html
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
