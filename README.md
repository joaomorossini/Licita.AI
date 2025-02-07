# Licita.AI

A Streamlit application for chatting with procurement documents using Dify.

## Setup

1. Install dependencies:

```bash
poetry install
```

2. Configure environment variables:

```bash
cp .env.example .env
```

Then edit `.env` and add your Dify API key.

3. Run the application:

```bash
poetry run streamlit run app.py
```

## Development

### Running Tests

```bash
poetry run pytest
```

### Project Structure

```
Licita.AI/
├── .env.example          # Template for environment variables
├── .env                  # Local environment variables (not in git)
├── README.md            # This file
├── app.py               # Application entry point
├── pyproject.toml       # Project dependencies
└── src/                 # Source code
    ├── __init__.py
    ├── main.py         # Main Streamlit application
    ├── chat_com_edital.py  # Chat interface
    └── dify_client.py  # Dify API client
```

---

### Poetry Export Command!

```zsh
export POETRY_VIRTUALENVS_PATH=/Users/morossini/anaconda3/envs/licita-ai-new
```
