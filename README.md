# MCP Chat

MCP Chat is a command-line interface application that enables interactive chat capabilities with AI models through the Anthropic API. The application supports document retrieval, command-based prompts, and extensible tool integrations via the MCP (Model Control Protocol) architecture.

## Prerequisites

- Python 3.9+
- Gemini API Key

## Setup

### Step 1: Configure the environment variables

1. Create or edit the `.env` file in the project root and verify that the following variables are set correctly:

```
GEMINI_MODEL="" # Enter Gemini Model
GEMINI_API_KEY=""  # Enter your Gemini API secret key

# Set to 1 if you're using uv to run the project
# Set to 0 if you're *not* using uv
USE_UV=1
```

### Step 2: Install dependencies

#### Option 1: Setup with uv (Recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package installer and resolver.

1. Install uv, if not already installed:

```bash
pip install uv
```

2. Create and activate a virtual environment:

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:

```bash
uv pip install -e .
uv pip install google-genai
```

4. Run the project

```bash
uv run main.py
```

#### Option 2: Setup without uv

1. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install anthropic google-genai python-dotenv prompt-toolkit "mcp[cli]==1.8.0"
```

3. Run the project

```bash
python main.py
```

## Usage

### Basic Interaction

Simply type your message and press Enter to chat with the model.

The assistant has access to MCP tools, allowing it to perform tasks such as:

- Reading files from your project
- Editing existing files
- Retrieving document contents
- Executing commands exposed by the MCP server

For example, you can ask:

```
> Read the README.md file
> Update the introduction in README.md
> Explain the contents of config.py
```

### Document Retrieval

Use the `@` symbol followed by a document ID to include document content in your query:

```
> Tell me about @deposition.md
```

### Commands

Use the `/` prefix to execute commands defined in the MCP server:

```
> /format deposition.md
```

Commands will auto-complete when you press **Tab**.

## MCP Inspector

This project defines its MCP tools, prompts, and resources in `mcp_server.py`.

To launch the MCP Inspector and interact with the server, run:

```bash
uv run mcp dev mcp_server.py
```

The MCP Inspector allows you to:

- Inspect the available tools
- View registered prompts
- Browse available resources
- Test tool execution interactively

Any tools, prompts, or resources you add to `mcp_server.py` will automatically be available in the inspector.
