"""
Test DigestGenerator initialization to check API key passthrough
"""
import os
from pathlib import Path
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment from learning-coach-mcp/.env
env_path = Path(__file__).parent / "learning-coach-mcp" / ".env"
load_dotenv(env_path)

openai_key = os.getenv("OPENAI_API_KEY")
logger.info(f"OpenAI API key loaded: {bool(openai_key)}")
logger.info(f"OpenAI API key (first 15 chars): {openai_key[:15] if openai_key else 'None'}")

# Import DigestGenerator
from rag.digest_generator import DigestGenerator

# Initialize
logger.info("\n" + "="*60)
logger.info("Initializing DigestGenerator...")
logger.info("="*60)

generator = DigestGenerator(
    supabase_url=os.getenv("SUPABASE_URL"),
    supabase_key=os.getenv("SUPABASE_KEY"),
    openai_api_key=openai_key,
    ragas_min_score=0.70,
)

logger.info("\n" + "="*60)
logger.info("✅ DigestGenerator initialized successfully")
logger.info(f"Evaluator type: {type(generator.evaluator)}")
logger.info(f"Evaluator faithfulness LLM: {getattr(generator.evaluator.faithfulness, 'llm', 'N/A')}")
logger.info("="*60)
