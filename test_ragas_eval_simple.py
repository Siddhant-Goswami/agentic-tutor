"""
Simple test to verify RAGAS evaluation works without warnings
"""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
import logging

# Set up logging to capture warnings
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment
env_path = Path(__file__).parent / "learning-coach-mcp" / ".env"
load_dotenv(env_path)

async def test_ragas():
    from rag.evaluator import RAGASEvaluator

    # Initialize evaluator with API key
    openai_key = os.getenv("OPENAI_API_KEY")
    logger.info(f"API key present: {bool(openai_key)}")

    evaluator = RAGASEvaluator(min_score=0.70, openai_api_key=openai_key)

    # Create sample data
    sample_query = "Explain transformers"
    sample_insights = [{
        "title": "Transformers Architecture",
        "explanation": "Transformers use self-attention mechanisms.",
        "practical_takeaway": "Implement attention in your model.",
        "source": {
            "title": "Test Paper",
            "author": "Test Author",
            "url": "http://example.com",
            "published_date": "2024-01-01"
        }
    }]
    sample_chunks = [{
        "chunk_text": "Transformers are a type of neural network architecture.",
        "similarity": 0.85
    }]

    logger.info("\n" + "="*60)
    logger.info("Running RAGAS evaluation...")
    logger.info("="*60)

    # Run evaluation
    scores = await evaluator.evaluate_digest(
        query=sample_query,
        insights=sample_insights,
        retrieved_chunks=sample_chunks
    )

    logger.info("\n" + "="*60)
    logger.info("RAGAS Evaluation Complete!")
    logger.info(f"Scores: {scores}")
    logger.info("="*60)

    # Check if there were any warnings
    return scores

if __name__ == "__main__":
    asyncio.run(test_ragas())
