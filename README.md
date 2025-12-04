# 🎓 AI Learning Coach

> **An autonomous AI-powered learning assistant** that delivers personalized daily insights, manages your learning journey, and adapts to your progress using advanced RAG (Retrieval-Augmented Generation) and agentic workflows.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-64%20passing-brightgreen.svg)](./tests)
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
git clone <your-repo-url>
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
- **Modular architecture** with 64 passing tests (Phase 3 refactored!)
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

```
┌─────────────────────────────────────────────────────────┐
│                   User Interfaces                       │
│  Dashboard (Streamlit) │ Claude Desktop │ Python API   │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│              Autonomous Agent (SENSE-PLAN-ACT)          │
│  • LLM Planning    • Tool Registry    • Reflection     │
│  • State Machine   • Audit Logging    • Quality Gates  │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│                  RAG Pipeline (Phase 3)                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │  Core    │  │Synthesis │  │Evaluation│             │
│  │ LLM      │  │ Prompt   │  │ RAGAS    │             │
│  │ Client   │  │ Builder  │  │ Metrics  │             │
│  └──────────┘  └──────────┘  └──────────┘             │
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
- **Agent Framework**: Custom autonomous loop with OpenAI GPT-4o
- **RAG System**: Modular architecture (64 tests, 100% passing)
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
from agent.controller import AgentController, AgentConfig

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

---

## 🛠️ Development

### Project Structure

```
agentic-tutor/
├── agent/                      # Autonomous agent (SENSE-PLAN-ACT)
│   ├── controller.py          # Main agent loop
│   ├── tools.py               # Tool registry
│   ├── logger.py              # Audit logging
│   └── prompts/               # LLM prompts
├── learning-coach-mcp/        # RAG & MCP server
│   └── src/
│       ├── rag/               # RAG system (Phase 3 refactored!)
│       │   ├── core/          # LLM client, base classes
│       │   ├── synthesis/     # Insight generation
│       │   ├── evaluation/    # RAGAS metrics
│       │   └── retrieval/     # Vector search
│       ├── server.py          # MCP server
│       └── utils/             # Shared utilities
├── dashboard/                 # Streamlit UI
│   ├── app.py                # Main app
│   └── views/                # Pages
├── database/                  # SQL migrations
│   └── migrations/
├── tests/                     # Test suite (64 tests!)
│   └── unit/rag/             # RAG unit tests
└── docs/                      # Documentation
```

### Running Tests

```bash
# Run all tests
pytest

# Run RAG tests
pytest tests/unit/rag/ -v

# Run with coverage
pytest --cov=src --cov-report=html
```

**Current Status:** 64/64 tests passing (100%) ✅

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

### Understanding the Codebase
- Start with [CODEBASE_GUIDE.md](./docs/CODEBASE_GUIDE.md)
- Read [ARCHITECTURE.md](./docs/ARCHITECTURE.md) for system design
- Check [agent/README.md](./agent/README.md) for agent details
- Review [Phase 3 refactoring docs](./.claude/tasks/PHASE3_COMPLETION.md)

### Key Concepts
- **RAG (Retrieval-Augmented Generation)**: Combines vector search with LLM synthesis
- **MCP (Model Context Protocol)**: Connects Claude Desktop to external tools
- **Autonomous Agents**: Self-planning systems using SENSE-PLAN-ACT loops
- **Vector Embeddings**: Semantic search using OpenAI text-embedding-3-small
- **RAGAS**: Quality evaluation framework for RAG systems

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
- **100xEngineers AI Bootcamp** - For the learning journey
- **Claude** - For pair programming this entire project
- **Open source community** - For amazing tools and libraries

---

## 🌟 Star History

If you find this project helpful, please consider giving it a star! ⭐

---

## 📞 Contact

- **Issues**: [GitHub Issues](https://github.com/yourusername/agentic-tutor/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/agentic-tutor/discussions)
- **Email**: your-email@example.com

---

**Made with ❤️ by [Your Name]**

**Happy Learning! 🚀📚**
