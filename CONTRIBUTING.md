# Contributing to AI Learning Coach

Thank you for considering contributing to AI Learning Coach! 🎉

This document will guide you through the contribution process, from setting up your development environment to submitting your first pull request. **Don't worry if you're new to open source** - we'll walk you through everything step by step!

---

## 📖 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Workflow](#development-workflow)
- [Code Style Guide](#code-style-guide)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Getting Help](#getting-help)

---

## 📜 Code of Conduct

This project follows a simple code of conduct:

- **Be respectful** - Treat everyone with kindness and respect
- **Be helpful** - Support other contributors and users
- **Be constructive** - Provide feedback that helps improve the project
- **Be patient** - Remember that everyone was a beginner once

By participating, you agree to uphold these values.

---

## 🚀 Getting Started

### 1. Prerequisites

Before you start, make sure you have:

- **Python 3.10 or higher** installed
- **Git** installed and configured
- A **GitHub account**
- **Basic Python knowledge** (you don't need to be an expert!)
- **Code editor** (VS Code, PyCharm, or any editor you prefer)

### 2. Fork the Repository

1. Go to the [AI Learning Coach repository](https://github.com/yourusername/agentic-tutor)
2. Click the **Fork** button in the top-right corner
3. This creates your own copy of the repository

### 3. Clone Your Fork

```bash
# Clone your fork to your local machine
git clone https://github.com/YOUR-USERNAME/agentic-tutor.git
cd agentic-tutor

# Add the original repository as 'upstream'
git remote add upstream https://github.com/ORIGINAL-OWNER/agentic-tutor.git

# Verify remotes
git remote -v
# Should show:
# origin    https://github.com/YOUR-USERNAME/agentic-tutor.git (fetch)
# origin    https://github.com/YOUR-USERNAME/agentic-tutor.git (push)
# upstream  https://github.com/ORIGINAL-OWNER/agentic-tutor.git (fetch)
# upstream  https://github.com/ORIGINAL-OWNER/agentic-tutor.git (push)
```

### 4. Set Up Development Environment

```bash
# Create a virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
cd learning-coach-mcp
pip install -e .
pip install -e ".[dev]"  # Install dev dependencies

# Install pre-commit hooks (optional but recommended)
pre-commit install
```

### 5. Configure Environment

```bash
# Copy example env file
cp learning-coach-mcp/.env.example learning-coach-mcp/.env

# Edit .env with your credentials
# (See README.md for where to get these)
```

### 6. Verify Setup

```bash
# Run tests to make sure everything works
pytest tests/unit/rag/ -v

# Should see: 64/64 tests passing ✅
```

**🎉 You're all set!** Ready to start contributing.

---

## 🤝 How Can I Contribute?

There are many ways to contribute, even if you're not a Python expert:

### For Beginners

#### 1. **Documentation** 📝
- Fix typos or unclear explanations
- Add examples or clarifications
- Improve installation instructions
- Write tutorials or guides
- Translate documentation

**Example:**
```markdown
<!-- Before -->
Run the server

<!-- After -->
Run the server using this command:
\`\`\`bash
cd learning-coach-mcp
python -m src.server
\`\`\`
```

#### 2. **Bug Reports** 🐛
- Report issues you encounter
- Provide reproduction steps
- Share error messages and logs

**How to write a good bug report:**
- Use a clear, descriptive title
- Describe what you expected to happen
- Describe what actually happened
- Include steps to reproduce
- Share your environment (OS, Python version, etc.)

#### 3. **Feature Requests** 💡
- Suggest new features
- Propose improvements
- Share use cases

### For Intermediate Developers

#### 4. **Code Improvements** ✨
- Refactor code for clarity
- Add type hints
- Improve error messages
- Optimize performance

#### 5. **Testing** 🧪
- Add test cases
- Improve test coverage
- Write integration tests

#### 6. **Bug Fixes** 🔧
- Fix reported issues
- Handle edge cases
- Improve error handling

### For Advanced Developers

#### 7. **New Features** 🚀
- Implement planned features
- Add new tools or capabilities
- Enhance RAG pipeline

#### 8. **Architecture** 🏗️
- Improve system design
- Add new integrations
- Optimize database queries

---

## 💻 Development Workflow

### Step 1: Pick an Issue

1. Browse [open issues](https://github.com/yourusername/agentic-tutor/issues)
2. Look for issues labeled:
   - `good first issue` - Great for beginners
   - `help wanted` - We need your help!
   - `documentation` - Improve docs
   - `bug` - Fix a bug
   - `enhancement` - Add new feature

3. Comment on the issue saying you want to work on it
4. Wait for maintainer confirmation

**Don't see an issue you want?** Open a new one to discuss your idea first!

### Step 2: Create a Branch

```bash
# Make sure you're on main and it's up to date
git checkout main
git pull upstream main

# Create a new branch
git checkout -b feature/your-feature-name

# Good branch names:
# - feature/add-quiz-generation
# - fix/database-connection-error
# - docs/improve-readme
# - test/add-rag-tests
```

### Step 3: Make Your Changes

**Follow these guidelines:**

1. **Keep changes focused** - One issue per branch
2. **Write clear code** - Use descriptive variable names
3. **Add comments** - Explain complex logic
4. **Update docs** - If you change functionality
5. **Add tests** - For new features or bug fixes

**Example: Adding a new feature**

```python
# ✅ Good: Clear, well-documented
async def generate_quiz(
    self,
    topic: str,
    difficulty: str = "intermediate",
    num_questions: int = 5,
) -> Dict[str, Any]:
    """
    Generate a quiz based on learning topic.

    Args:
        topic: Subject for quiz questions
        difficulty: One of 'beginner', 'intermediate', 'advanced'
        num_questions: Number of questions to generate (1-10)

    Returns:
        Dictionary containing quiz questions and metadata

    Raises:
        ValueError: If difficulty is invalid or num_questions out of range
    """
    # Validate inputs
    if difficulty not in ["beginner", "intermediate", "advanced"]:
        raise ValueError(f"Invalid difficulty: {difficulty}")

    if not 1 <= num_questions <= 10:
        raise ValueError(f"num_questions must be 1-10, got {num_questions}")

    # Generate quiz
    # ...

# ❌ Bad: Unclear, no validation
async def gen_q(t, d="i", n=5):
    # do stuff
    pass
```

### Step 4: Commit Your Changes

```bash
# Stage your changes
git add .

# Commit with a clear message
git commit -m "feat: add quiz generation feature

- Add generate_quiz method to agent tools
- Include difficulty levels: beginner/intermediate/advanced
- Add validation for num_questions (1-10)
- Write 8 new tests for quiz generation

Closes #42"
```

**Commit Message Format:**

```
<type>: <short description>

<optional longer description>

<optional footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding or updating tests
- `refactor`: Code refactoring
- `style`: Code style changes (formatting, etc.)
- `chore`: Maintenance tasks

**Examples:**
```bash
git commit -m "fix: resolve database connection timeout issue"
git commit -m "docs: add examples to RAG pipeline guide"
git commit -m "test: add edge case tests for synthesizer"
git commit -m "refactor: extract prompt building to separate module"
```

### Step 5: Push to Your Fork

```bash
# Push your branch to your fork
git push origin feature/your-feature-name
```

### Step 6: Create Pull Request

1. Go to your fork on GitHub
2. Click **"Compare & pull request"** button
3. Fill in the PR template:
   - Clear title
   - Description of changes
   - Link to related issue
   - Screenshots (if UI changes)
   - Testing done

4. Click **"Create pull request"**

---

## 🎨 Code Style Guide

We follow modern Python best practices. Here are the key guidelines:

### Python Style

```python
# ✅ Use type hints
async def search_content(
    self,
    query: str,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """Search content with type hints."""
    pass

# ✅ Use descriptive names
user_learning_context = get_user_context(user_id)
retrieved_chunks = search_content(query)

# ❌ Avoid abbreviations
usr_ctx = get_ctx(uid)  # Too cryptic!

# ✅ Use docstrings for public methods
def validate_input(data: Dict[str, Any]) -> bool:
    """
    Validate user input data.

    Args:
        data: Dictionary containing user input

    Returns:
        True if valid, False otherwise
    """
    pass

# ✅ Handle errors gracefully
try:
    result = await llm_client.generate(prompt)
except Exception as e:
    logger.error(f"LLM generation failed: {e}")
    return {"error": "Failed to generate response"}

# ❌ Don't silence errors
try:
    result = await llm_client.generate(prompt)
except:  # Too broad!
    pass  # Error disappeared!
```

### File Organization

```python
# File: src/rag/synthesis/synthesizer.py

"""
Educational Synthesizer Module

This module handles synthesis of educational insights from retrieved content.
"""

# Standard library imports first
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

# Third-party imports second
from openai import AsyncOpenAI

# Local imports last
from src.rag.core.llm_client import LLMClient
from src.rag.synthesis.prompt_builder import PromptBuilder
from src.rag.synthesis.parsers import InsightParser

# Module logger
logger = logging.getLogger(__name__)

# Constants
DEFAULT_NUM_INSIGHTS = 7
DEFAULT_TEMPERATURE = 0.3

# Classes and functions follow...
```

### Code Formatting

We use **Black** for code formatting:

```bash
# Format your code
black .

# Check formatting
black --check .
```

Optional but recommended: Set up your editor to format on save.

---

## 🧪 Testing Guidelines

**All code changes should include tests!**

### Writing Tests

```python
# File: tests/unit/rag/synthesis/test_synthesizer.py

import pytest
from unittest.mock import Mock, AsyncMock

from src.rag.synthesis.synthesizer import EducationalSynthesizer


class TestEducationalSynthesizer:
    """Tests for EducationalSynthesizer class."""

    @pytest.mark.asyncio
    async def test_synthesize_insights_success(self):
        """Test successful insight synthesis."""
        # Arrange - Set up test data and mocks
        mock_llm = Mock()
        mock_llm.get_model_info.return_value = {"model": "gpt-4o"}
        mock_llm.generate = AsyncMock(return_value='{"insights": [...]}')

        synthesizer = EducationalSynthesizer(llm_client=mock_llm)

        chunks = [{"chunk_text": "Test content about AI"}]
        context = {"week": 1, "topics": ["AI"]}

        # Act - Execute the code being tested
        result = await synthesizer.synthesize_insights(
            retrieved_chunks=chunks,
            learning_context=context,
            query="What is AI?",
        )

        # Assert - Verify the results
        assert result is not None
        assert "insights" in result
        assert isinstance(result["insights"], list)

    @pytest.mark.asyncio
    async def test_synthesize_insights_empty_chunks(self):
        """Test handling of empty chunks."""
        mock_llm = Mock()
        mock_llm.get_model_info.return_value = {"model": "gpt-4o"}

        synthesizer = EducationalSynthesizer(llm_client=mock_llm)

        result = await synthesizer.synthesize_insights(
            retrieved_chunks=[],  # Empty!
            learning_context={"week": 1},
            query="test",
        )

        # Should handle gracefully
        assert result["insights"] == []
        assert "error" in result["metadata"]
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/rag/synthesis/test_synthesizer.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test
pytest tests/unit/rag/synthesis/test_synthesizer.py::TestEducationalSynthesizer::test_synthesize_insights_success
```

### Test Coverage

- Aim for **at least 80% coverage** for new code
- Test **happy path** (everything works)
- Test **edge cases** (empty inputs, None values, etc.)
- Test **error handling** (what happens when things fail)

---

## 🔄 Pull Request Process

### Before Submitting

**Checklist:**
- [ ] Code follows style guidelines
- [ ] Tests added and passing
- [ ] Documentation updated
- [ ] Commit messages are clear
- [ ] Branch is up to date with main

```bash
# Update your branch with latest main
git checkout main
git pull upstream main
git checkout feature/your-feature-name
git merge main

# Resolve any conflicts, then:
git push origin feature/your-feature-name
```

### PR Template

When creating a PR, fill in this information:

```markdown
## Description
Brief description of what this PR does

Fixes #(issue number)

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Code refactoring
- [ ] Test addition/update

## Changes Made
- List of specific changes
- Be clear and concise
- Use bullet points

## Testing Done
- Describe tests you ran
- Include test output if relevant

## Screenshots
(If applicable, add screenshots for UI changes)

## Checklist
- [ ] My code follows the project's style guidelines
- [ ] I have added tests that prove my fix/feature works
- [ ] All new and existing tests pass
- [ ] I have updated the documentation
- [ ] My commits follow the commit message guidelines
```

### Review Process

1. **Automated Checks** - CI/CD runs tests automatically
2. **Code Review** - Maintainers review your code
3. **Feedback** - You may get requests for changes
4. **Approval** - Once approved, your PR gets merged!

**During Review:**
- Respond to feedback constructively
- Make requested changes promptly
- Ask questions if something is unclear
- Be patient - reviews can take time

**Making Changes After Review:**

```bash
# Make the requested changes
# Stage and commit
git add .
git commit -m "fix: address review feedback

- Improve error handling
- Add missing docstrings
- Fix edge case in parser"

# Push to update the PR
git push origin feature/your-feature-name
```

---

## 🆘 Getting Help

### Questions About Contributing?

- **Check documentation** first (README, this guide, etc.)
- **Search existing issues** - your question may be answered
- **Ask in discussions** - GitHub Discussions is great for questions
- **Join community chat** - (if available)

### Stuck on Something?

**Don't be shy to ask for help!** Everyone gets stuck sometimes.

**How to ask for help:**
1. Describe what you're trying to do
2. Explain what you tried
3. Share relevant code/errors
4. Be specific about where you're stuck

**Example:**

> Hi! I'm working on #42 (quiz generation feature). I'm trying to test the quiz validation but getting this error:
> ```
> TypeError: 'Mock' object is not subscriptable
> ```
>
> Here's my test code:
> ```python
> mock_llm = Mock()
> synthesizer = EducationalSynthesizer(llm_client=mock_llm)
> ```
>
> I think I need to mock `get_model_info()` but not sure how. Any help appreciated!

### Resources

- [Python Type Hints Guide](https://docs.python.org/3/library/typing.html)
- [Pytest Documentation](https://docs.pytest.org/)
- [Git Basics Tutorial](https://git-scm.com/book/en/v2)
- [How to Write a Git Commit Message](https://chris.beams.io/posts/git-commit/)

---

## 🎯 Contribution Examples

### Example 1: Fixing a Typo (Easiest!)

```bash
# 1. Create branch
git checkout -b docs/fix-readme-typo

# 2. Fix the typo in README.md
# Change "teh" to "the"

# 3. Commit
git add README.md
git commit -m "docs: fix typo in README

Changed 'teh' to 'the' in Quick Start section"

# 4. Push
git push origin docs/fix-readme-typo

# 5. Create PR on GitHub
```

### Example 2: Adding a Test

```bash
# 1. Create branch
git checkout -b test/add-edge-case-for-parser

# 2. Add test in tests/unit/rag/synthesis/test_parsers.py
def test_parse_insights_with_unicode():
    """Test parser handles unicode characters."""
    parser = InsightParser()
    response = '{"insights": [{"title": "学习AI", "explanation": "..."}]}'

    result = parser.parse_insights(response)

    assert len(result) == 1
    assert "学习" in result[0]["title"]

# 3. Run test to verify
pytest tests/unit/rag/synthesis/test_parsers.py::test_parse_insights_with_unicode -v

# 4. Commit
git add tests/unit/rag/synthesis/test_parsers.py
git commit -m "test: add unicode handling test for InsightParser

Test ensures parser correctly handles non-ASCII characters
in insight titles and explanations."

# 5. Push and create PR
git push origin test/add-edge-case-for-parser
```

### Example 3: Adding a Feature

```bash
# 1. Open issue first to discuss the feature
# 2. Get approval from maintainers
# 3. Create branch
git checkout -b feature/add-difficulty-adjustment

# 4. Implement feature
# - Add code to agent/tools.py
# - Add tests to tests/unit/test_tools.py
# - Update docs in README.md

# 5. Run all tests
pytest

# 6. Commit (can be multiple commits)
git add agent/tools.py tests/unit/test_tools.py
git commit -m "feat: add difficulty adjustment based on quiz scores

- Add adjust_difficulty() method to AgentTools
- Automatically increases/decreases difficulty based on performance
- Add 6 tests covering all difficulty transitions
- Update README with new feature documentation

Closes #123"

# 7. Push and create PR
git push origin feature/add-difficulty-adjustment
```

---

## 🌟 Recognition

All contributors will be:
- Listed in [CONTRIBUTORS.md](./CONTRIBUTORS.md)
- Mentioned in release notes (for significant contributions)
- Given credit in the project documentation

---

## 📝 Final Notes

### Remember:

- **Start small** - Your first PR doesn't have to be perfect
- **Ask questions** - There are no stupid questions
- **Be patient** - Learning takes time
- **Have fun** - Contributing should be enjoyable!

### Thank You! 🙏

Every contribution, no matter how small, makes this project better. We truly appreciate your time and effort!

**Happy coding! 🚀**

---

**Questions?** Open an issue or start a discussion. We're here to help!
