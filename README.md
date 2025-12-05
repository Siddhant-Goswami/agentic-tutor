# 🎓 AI Learning Coach

> **An autonomous AI-powered learning assistant** that delivers personalized daily insights, manages your learning journey, and adapts to your progress using advanced RAG (Retrieval-Augmented Generation) and agentic workflows.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-131%20passing-brightgreen.svg)](./tests)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

---

## ✨ What Makes This Special?

This isn't just another chatbot - it's a **fully autonomous agent** that:
- 🧠 **Thinks and plans** its own actions using the SENSE → PLAN → ACT → OBSERVE → REFLECT loop
- 📚 **Learns from your progress** and adapts difficulty based on your current learning context
- 🔍 **Searches and synthesizes** insights from curated content sources using advanced vector search
- ✅ **Evaluates quality** using RAGAS metrics (faithfulness, precision, recall)
- 💬 **Works everywhere** - Streamlit dashboard, Claude Desktop (MCP), or standalone Python

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- [Supabase](https://supabase.com) account (free tier)
- OpenAI API key ([get one here](https://platform.openai.com/api-keys))
- Optional: [Claude Desktop](https://claude.ai/download) for MCP integration

### 5-Minute Setup

```bash
# 1. Clone the repository
git clone https://github.com/Siddhant-Goswami/agentic-tutor.git
cd agentic-tutor

# 2. Install dependencies
cd learning-coach-mcp
pip install -e .

# 3. Set up environment
cp .env.example .env
# Edit .env with your credentials (see Configuration section)

# 4. Set up database (run migrations in Supabase SQL Editor)
# See Database Setup section below

# 5. Test it works
cd ..
python test_agent.py
```

**🎉 That's it!** You now have a working AI learning coach.

---

## 📖 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Installation](#️-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Development](#-development)
- [Contributing](#-contributing)
- [Documentation](#-documentation)
- [Troubleshooting](#-troubleshooting)

---

## 🎯 Features

### 🤖 Autonomous Agent
- **SENSE → PLAN → ACT → OBSERVE → REFLECT** loop for autonomous decision-making
- Multi-step reasoning with LLM-powered planning
- Self-correcting behavior with quality checks
- Tool approval workflow for user confirmation

### 📚 Intelligent RAG System
- **Vector search** with OpenAI embeddings (text-embedding-3-small)
- **Semantic retrieval** using Supabase pgvector + HNSW index
- **Modular architecture** with 131 passing tests (fully refactored!)
- **Quality evaluation** using RAGAS metrics
- **Template-based prompts** for easy customization

### 🎓 Personalized Learning
- **Daily digest** generation with 7 educational insights
- **Context-aware** synthesis (tracks week, topics, difficulty, goals)
- **Past insights search** to review previous learning
- **Feedback system** to improve future recommendations
- **Bootcamp progress sync** to stay aligned with your curriculum

### 🔌 Multi-Interface Support
- **Streamlit Dashboard** - Beautiful web UI with live agent monitoring
- **Claude Desktop (MCP)** - Natural language interaction
- **Standalone Python** - Programmatic access via API
- **REST API** - Future HTTP endpoint support

---

## 🏗️ Architecture

### 🎯 Library + Applications Pattern

Think of this project like your phone:
- **`src/`** = The operating system (iOS/Android) - the core "brain" with all the smart algorithms
- **`dashboard/`** = An app on your phone (like Instagram) - uses the OS
- **`learning-coach-mcp/`** = Another app (like WhatsApp) - also uses the OS
- **`tests/`** = Quality control that tests the OS works correctly

**Why this structure?**
- ✅ **Single source of truth**: All logic lives in `src/`, no duplication
- ✅ **Easy to test**: `src/` is a pure library with 131 tests
- ✅ **Multiple interfaces**: Dashboard, MCP server, Python API all use the same core
- ✅ **Clean & modular**: Each app is slim, just UI/integration code

```
┌─────────────────────────────────────────────────────────┐
│                   User Interfaces                       │
│  Dashboard (Streamlit) │ Claude Desktop │ Python API   │
│         ↓                      ↓                ↓       │
│    (imports from src/)   (imports from src/)           │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│             📦 src/ - Core Library (THE BRAIN)          │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  🤖 src/agent/ - Autonomous Agent System       │   │
│  │  • SENSE → PLAN → ACT → OBSERVE → REFLECT      │   │
│  │  • Tool Registry  • Step Executor  • Logger    │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  📚 src/rag/ - RAG Pipeline (Fully Modular)    │   │
│  │  • Core (LLM Client, Base Classes)              │   │
│  │  • Synthesis (Insight Generation)               │   │
│  │  • Evaluation (RAGAS Metrics)                   │   │
│  │  • Retrieval (Vector Search, Query Building)   │   │
│  │  • Digest (Daily Digest Generator)              │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  💾 src/database/ - Database Utilities         │   │
│  │  • Supabase client creation                     │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  🔧 src/core/ - Infrastructure                 │   │
│  │  • Config  • Exceptions  • Types                │   │
│  └─────────────────────────────────────────────────┘   │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│            Supabase Database + pgvector                 │
│  • Vector embeddings (HNSW index)                       │
│  • Learning context & progress                          │
│  • Content sources & digests                            │
│  • Row-level security (RLS)                             │
└─────────────────────────────────────────────────────────┘
```

### Key Technologies
- **Core Library**: `src/` with 100% type hints, protocol-based design
- **Agent Framework**: Custom autonomous loop with OpenAI GPT-4o
- **RAG System**: Modular architecture (131 tests, 98.5% passing)
- **Vector DB**: Supabase pgvector with HNSW indexing
- **LLM**: OpenAI (embeddings + synthesis) or Anthropic Claude
- **Frontend**: Streamlit with real-time agent monitoring
- **MCP**: FastMCP for Claude Desktop integration

---

## ⚙️ Installation

### Step 1: Clone Repository
```bash
git clone <your-repo-url>
cd agentic-tutor
```

### Step 2: Install Python Dependencies
```bash
cd learning-coach-mcp
pip install -e .
```

This installs:
- OpenAI SDK
- Anthropic SDK (optional)
- Supabase client
- FastMCP (for Claude Desktop)
- RAGAS (for evaluation)
- Streamlit (for dashboard)

### Step 3: Database Setup

1. **Create Supabase Project**
   - Go to [supabase.com](https://supabase.com)
   - Create new project (free tier works!)
   - Note your project URL and API key

2. **Run Migrations**

   Open **SQL Editor** in Supabase and run these files in order:

   ```sql
   -- File: database/migrations/001_initial_schema.sql
   -- Creates tables, indexes, and enables pgvector

   -- File: database/migrations/003_insert_test_data_with_rls_bypass.sql
   -- Adds test user and sample data

   -- File: database/migrations/004_add_test_user_rls_policies.sql
   -- Configures row-level security
   ```

### Step 4: Configuration

Create `.env` file in `learning-coach-mcp/`:

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here

# OpenAI
OPENAI_API_KEY=sk-proj-your-key-here

# Anthropic (Optional)
# ANTHROPIC_API_KEY=sk-ant-your-key-here

# User
DEFAULT_USER_ID=00000000-0000-0000-0000-000000000001

# Agent Config (Optional)
AGENT_MAX_ITERATIONS=10
AGENT_LLM_MODEL=gpt-4o
AGENT_TEMPERATURE=0.3
```

**Getting Credentials:**
- **Supabase**: Settings → API → Copy Project URL & anon key
- **OpenAI**: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)

---

## 🎮 Usage

### Option 1: Streamlit Dashboard (Recommended for beginners)

```bash
cd dashboard
streamlit run app.py
```

Opens at: **http://localhost:8501**

**Features:**
- 🏠 **Home**: View today's digest, real-time agent logs
- 🎯 **Agent**: Interactive agent playground with approval workflow
- ⚙️ **Settings**: Update learning context, manage sources
- 📊 **Analytics**: View quality metrics and usage stats

### Option 2: Claude Desktop (MCP)

1. **Configure Claude Desktop**

   Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

   ```json
   {
     "mcpServers": {
       "learning-coach": {
         "command": "/path/to/python3",
         "args": ["-m", "src.server"],
         "cwd": "/absolute/path/to/learning-coach-mcp",
         "env": {
           "SUPABASE_URL": "https://your-project.supabase.co",
           "SUPABASE_KEY": "your-key",
           "OPENAI_API_KEY": "sk-proj-your-key"
         }
       }
     }
   }
   ```

2. **Restart Claude Desktop**

3. **Use Natural Language**
   ```
   You: Generate my daily learning digest
   Claude: [Uses agent tool to create personalized insights]

   You: Search my past insights about transformers
   Claude: [Searches your learning history]
   ```

### Option 3: Python API

```python
from src.agent.controllers.agent_controller import AgentController
from src.agent.models.agent_config import AgentConfig

# Configure
config = AgentConfig(
    max_iterations=10,
    llm_model="gpt-4o",
    temperature=0.3,
)

# Initialize
controller = AgentController(
    config=config,
    supabase_url="https://your-project.supabase.co",
    supabase_key="your-key",
    openai_api_key="your-key",
)

# Run
result = await controller.run(
    goal="Generate my daily learning digest",
    user_id="your-user-id",
)

print(result.output)  # Final digest
print(result.logs)    # Execution trace
```

**Want to use the RAG system directly?**

```python
from src.rag.digest import DigestGenerator
import datetime

# Create digest generator
generator = DigestGenerator(
    supabase_url="https://your-project.supabase.co",
    supabase_key="your-key",
    openai_api_key="your-key",
)

# Generate today's digest
digest = await generator.generate(
    user_id="your-user-id",
    date=datetime.now().date(),
    max_insights=7,
)

print(f"Generated {len(digest['insights'])} insights!")
print(f"Quality: {digest['quality_badge']}")  # ✨ (high quality)
```

---

## 🛠️ Development

### Project Structure

```
agentic-tutor/
├── src/                        🧠 CORE LIBRARY (The Brain)
│   ├── agent/                 # Autonomous agent system
│   │   ├── controllers/       # AgentController, StepExecutor
│   │   ├── models/            # AgentConfig, AgentResult
│   │   ├── tools/             # ToolRegistry (search, context, etc.)
│   │   ├── utils/             # Logger, parsers
│   │   ├── planning/          # ResearchPlanner
│   │   └── prompts/           # LLM prompt templates
│   ├── rag/                   # RAG pipeline (fully modular!)
│   │   ├── core/              # LLMClient, base classes
│   │   ├── synthesis/         # EducationalSynthesizer
│   │   ├── evaluation/        # InsightEvaluator, RAGAS
│   │   ├── retrieval/         # VectorRetriever, QueryBuilder
│   │   └── digest/            # DigestGenerator, QualityGate
│   ├── database/              # Database utilities
│   │   └── client.py          # Supabase connection helpers
│   └── core/                  # Infrastructure
│       ├── config.py          # App configuration
│       ├── exceptions.py      # Error handling
│       └── types.py           # Type definitions
│
├── dashboard/                  📱 APPLICATION: Streamlit UI
│   ├── app.py                 # Main app (imports from src/)
│   └── views/                 # Pages
│       ├── home.py            # Today's digest
│       ├── agent.py           # Agent playground
│       └── settings.py        # Configuration
│
├── learning-coach-mcp/         📱 APPLICATION: MCP Server
│   ├── src/
│   │   ├── server.py          # MCP tools (imports from src/)
│   │   ├── db/                # Migrations
│   │   ├── integrations/      # Bootcamp sync
│   │   ├── ingestion/         # Content ingestion
│   │   ├── ui/                # UI templates
│   │   └── tools/             # MCP tool definitions
│   └── pyproject.toml         # Package config
│
├── database/                   💾 SQL MIGRATIONS
│   └── migrations/            # Supabase schema
│
├── tests/                      ✅ TEST SUITE (131 tests!)
│   ├── unit/                  # Unit tests for src/
│   │   ├── agent/             # Agent tests
│   │   ├── rag/               # RAG tests
│   │   └── core/              # Core tests
│   ├── integration/           # Integration tests
│   └── e2e/                   # End-to-end tests
│
└── docs/                       📚 DOCUMENTATION
    ├── ARCHITECTURE.md        # System design
    ├── CODEBASE_GUIDE.md      # Code walkthrough
    └── ...

```

**🎯 Key Principles:**
1. **`src/`** = Pure library with all logic (100% type hints, tested)
2. **`dashboard/`** = Thin UI layer using `src/`
3. **`learning-coach-mcp/`** = Thin MCP layer using `src/`
4. **No code duplication** - everything imports from `src/`

See [`src/README.md`](./src/README.md) for detailed architecture guide!

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test suites
pytest tests/unit/agent/ -v      # Agent tests
pytest tests/unit/rag/ -v        # RAG tests
pytest tests/unit/core/ -v       # Core tests
pytest tests/integration/ -v     # Integration tests

# Run with coverage
pytest --cov=src --cov-report=html
```

**Current Status:** 131/133 tests passing (98.5%) ✅

**Test Coverage:**
- ✅ Agent system: Controllers, tools, planning
- ✅ RAG pipeline: Synthesis, evaluation, retrieval, digest
- ✅ Database utilities
- ✅ Core infrastructure
- ✅ Integration tests

### Code Quality

We follow modern Python best practices:
- ✅ Type hints everywhere (`mypy` compatible)
- ✅ Protocol-based interfaces
- ✅ Dependency injection
- ✅ Comprehensive error handling
- ✅ Extensive logging
- ✅ Template-based prompts

### Making Changes

1. **Read** [CONTRIBUTING.md](./CONTRIBUTING.md) first!
2. **Create branch** from `main`
3. **Make changes** following code style
4. **Add tests** for new functionality
5. **Run tests** to verify
6. **Submit PR** with clear description

---

## 🤝 Contributing

We welcome contributions! Whether you're:
- 🐛 Fixing a bug
- ✨ Adding a feature
- 📝 Improving documentation
- 🧪 Writing tests

**Please read [CONTRIBUTING.md](./CONTRIBUTING.md)** for detailed guidelines.

### Quick Start for Contributors
1. Fork the repository
2. Clone your fork
3. Create a feature branch
4. Make your changes
5. Run tests
6. Submit a pull request

See [CONTRIBUTING.md](./CONTRIBUTING.md) for the full guide.

---

## 📚 Documentation

### For Users
- [Quick Start Guide](./docs/QUICK_START.md) - Get up and running fast
- [User Guide](./docs/USER_GUIDE.md) - Complete feature walkthrough
- [Troubleshooting](./docs/TROUBLESHOOTING.md) - Common issues & solutions

### For Developers
- [Architecture Guide](./docs/ARCHITECTURE.md) - System design deep dive
- [Codebase Guide](./docs/CODEBASE_GUIDE.md) - Code walkthrough
- [Contributing Guide](./CONTRIBUTING.md) - How to contribute
- [Phase 3 Migration](./docs/PHASE3_MIGRATION.md) - RAG refactoring guide

### Technical Documentation
- [Phase 3 Completion Summary](./.claude/tasks/PHASE3_COMPREHENSIVE_REVIEW_SUMMARY.md)
- [Edge Case Analysis](./.claude/tasks/PHASE3_EDGE_CASE_ANALYSIS.md)
- [Agent Implementation](./.claude/tasks/agentic-learning-coach-implementation-plan.md)

---

## 🐛 Troubleshooting

### Common Issues

#### MCP Server Not Connecting
```bash
# Find Python path
which python3

# Use full path in claude_desktop_config.json
"/Users/yourname/miniconda3/bin/python3"

# Restart Claude Desktop completely
```

#### Database Connection Errors
```bash
# Verify credentials
echo $SUPABASE_URL
echo $SUPABASE_KEY

# Check migrations ran
# Go to Supabase → SQL Editor → Run migrations in order
```

#### No Insights Generated
```bash
# Check OpenAI key
echo $OPENAI_API_KEY

# Verify content in database
# Dashboard → Settings → System → Check stats

# Run ingestion
cd learning-coach-mcp
python -m src.ingestion.rss_ingestion
```

### Getting Help

1. Check [Troubleshooting Guide](./docs/TROUBLESHOOTING.md)
2. Search [existing issues](https://github.com/yourusername/agentic-tutor/issues)
3. Open a [new issue](https://github.com/yourusername/agentic-tutor/issues/new) with:
   - Clear description
   - Steps to reproduce
   - Error messages
   - Environment details

---

## 🎓 Learning Resources

### 📖 For Beginners - Start Here!
1. **[src/README.md](./src/README.md)** - Beginner-friendly guide to the core library
   - Phone OS analogy for architecture
   - Simple code examples
   - Key concepts explained (Protocols, Type Hints, Dependency Injection)
   - Troubleshooting guide

2. **Main README** (this file) - Project overview and setup

3. **[Migration Story](./.claude/tasks/MIGRATION_COMPLETE.md)** - Complete refactoring journey
   - Why we refactored to `src/`
   - Before/after comparison
   - Benefits achieved

### 🔧 For Developers
- [CODEBASE_GUIDE.md](./docs/CODEBASE_GUIDE.md) - Code walkthrough
- [ARCHITECTURE.md](./docs/ARCHITECTURE.md) - System design deep dive
- [src/README.md](./src/README.md) - Core library architecture
- [CONTRIBUTING.md](./CONTRIBUTING.md) - How to contribute

### 🧠 Key Concepts Explained

**RAG (Retrieval-Augmented Generation)**
- Combines vector search with LLM synthesis
- Finds relevant content using semantic similarity
- Generates insights using OpenAI/Anthropic
- Quality checked with RAGAS metrics

**Autonomous Agents**
- Self-planning systems using SENSE → PLAN → ACT → OBSERVE → REFLECT
- Makes decisions using LLM reasoning
- Uses tools to accomplish goals
- See `src/agent/` for implementation

**MCP (Model Context Protocol)**
- Connects Claude Desktop to external tools
- Natural language interface to the agent
- See `learning-coach-mcp/src/server.py`

**Vector Embeddings**
- Converts text to numerical vectors
- Enables semantic search (meaning-based, not keyword)
- Uses OpenAI text-embedding-3-small
- Stored in Supabase pgvector with HNSW index

**Protocol-Based Design**
- Python protocols define contracts (like TypeScript interfaces)
- Enables swapping implementations easily
- Makes code testable with mocks
- See `src/rag/core/base_synthesizer.py` for examples

---

## 📄 License

MIT License - See [LICENSE](./LICENSE) file for details.

---

## 🙏 Acknowledgments

Built with love using:
- [OpenAI](https://openai.com) - Embeddings & LLM
- [Anthropic Claude](https://anthropic.com) - Alternative LLM
- [Supabase](https://supabase.com) - Vector database
- [FastMCP](https://github.com/jlowin/fastmcp) - MCP framework
- [RAGAS](https://github.com/explodinggradients/ragas) - RAG evaluation
- [Streamlit](https://streamlit.io) - Dashboard UI

Special thanks to:
- **100xEngineers Team** - For the learning journey
- **Claude** - For pair programming this project
- **Open source community** - For amazing tools and libraries

---

If you find this project helpful, please consider giving it a star! ⭐

---

## 📞 Contact

- **Issues**: [GitHub Issues](https://github.com/yourusername/agentic-tutor/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/agentic-tutor/discussions)
- **Email**: siddhant@100xengineers.com

---

**Made with ❤️ by Siddhant Goswami and Claude Code**
