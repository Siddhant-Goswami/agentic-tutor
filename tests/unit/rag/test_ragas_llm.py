"""
Test RAGAS LLM initialization
"""
import os
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Import the evaluator
from rag.evaluator import RAGASEvaluator

# Get API key
openai_api_key = os.getenv("OPENAI_API_KEY")
logger.info(f"OpenAI API key present: {bool(openai_api_key)}")
logger.info(f"OpenAI API key (first 10 chars): {openai_api_key[:10] if openai_api_key else 'None'}")

# Initialize evaluator
logger.info("Initializing RAGASEvaluator with API key...")
evaluator = RAGASEvaluator(min_score=0.70, openai_api_key=openai_api_key)

# Check if metrics have LLM
logger.info(f"Faithfulness metric: {evaluator.faithfulness}")
logger.info(f"Context precision metric: {evaluator.context_precision}")
logger.info(f"Context recall metric: {evaluator.context_recall}")

# Try to check if the LLM is set
if hasattr(evaluator.faithfulness, 'llm'):
    logger.info(f"Faithfulness has LLM: {evaluator.faithfulness.llm}")
else:
    logger.info("Faithfulness does not have llm attribute")

logger.info("✅ Test complete")
