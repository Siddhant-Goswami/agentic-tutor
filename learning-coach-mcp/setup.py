"""
Setup configuration for learning-coach-mcp package.
"""

from setuptools import setup, find_packages

setup(
    name="learning-coach-mcp",
    version="0.1.0",
    description="AI Learning Coach MCP Server with RAG capabilities",
    author="Your Name",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.9",
    install_requires=[
        "anthropic>=0.18.0",
        "openai>=1.12.0",
        "supabase>=2.3.0",
        "ragas>=0.1.0",
        "python-dotenv>=1.0.0",
        "mcp>=0.1.0",
    ],
)
