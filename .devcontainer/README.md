# Dev Container Configuration

This directory contains the configuration files for VS Code Dev Containers, allowing you to develop this project in a consistent, containerized environment.

## Files

- **devcontainer.json**: VS Code Dev Container configuration
- **Dockerfile**: Docker image definition for the development environment

## Prerequisites

1. **Docker**: Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) for your operating system
2. **VS Code**: Install [Visual Studio Code](https://code.visualstudio.com/)
3. **Dev Containers Extension**: Install the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) for VS Code

## Getting Started

1. Open this repository in VS Code
2. When prompted, click "Reopen in Container" or run the command:
   - Press `F1` or `Ctrl+Shift+P` (Windows/Linux) / `Cmd+Shift+P` (Mac)
   - Type: `Dev Containers: Reopen in Container`
   - Select it from the dropdown

3. VS Code will build the Docker image and start the container (this may take a few minutes on first run)
4. Once ready, you'll be inside the containerized development environment

## What's Included

### Base Environment
- Python 3.12
- Git, curl, vim, nano
- Non-root user (`vscode`) for security

### VS Code Extensions
- Python support (ms-python.python)
- Pylance for IntelliSense
- Black formatter
- Jupyter notebooks
- Docker extension
- GitLens
- Code spell checker

### Python Packages
All packages from `requirements.txt` are automatically installed, including:
- langchain
- langgraph
- langchain-openai
- langsmith
- tavily-python
- python-dotenv

## Environment Variables

Remember to create a `.env` file in the root directory with your API keys:

```ini
# LLM Providers
OPENROUTER_API_KEY=sk-or-...
OPENAI_API_KEY=sk-...

# Search Providers
TAVILY_API_KEY=tvly-...

# Metricool (for posting)
METRICOOL_API=...
METRICOOL_USER_ID=...
METRICOOL_BLOG_ID=...

# Feature Flags
ENABLE_POSTING=false

# LangSmith Tracing
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT="https://api.smith.langchain.com"
LANGCHAIN_API_KEY=lsv2-...
LANGCHAIN_PROJECT="social-media-agent"
```

## Running the Project

Once inside the dev container:

```bash
# Run the main workflow
python main.py

# Run tests
python tests/test_saver.py
python tests/verify_saver.py
```

## Customization

You can customize the dev container by editing:
- **devcontainer.json**: Add more VS Code extensions, change settings, or modify the configuration
- **Dockerfile**: Install additional system packages or change the base image

After making changes, rebuild the container:
- Press `F1` / `Ctrl+Shift+P` / `Cmd+Shift+P`
- Run: `Dev Containers: Rebuild Container`

## Troubleshooting

### Container fails to build
- Ensure Docker is running
- Check Docker has enough resources (memory/disk space)
- Try rebuilding: `Dev Containers: Rebuild Container Without Cache`

### Python packages not installed
- The `postCreateCommand` should install packages automatically
- If it fails, manually run: `pip install -r requirements.txt`

### Permission issues
- The container uses a non-root user (`vscode`)
- If you need root access, use: `sudo <command>`

## More Information

- [VS Code Dev Containers Documentation](https://code.visualstudio.com/docs/devcontainers/containers)
- [Dev Container Specification](https://containers.dev/)
