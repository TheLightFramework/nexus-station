import logging
from functools import lru_cache
from typing import List

# Try to import sentence_transformers, handle missing lib gracefully
try:
    from sentence_transformers import SentenceTransformer, util
    HAS_VECTORS = True
except ImportError:
    HAS_VECTORS = False

print("Has vectors value: ", HAS_VECTORS)

# CONFIGURE LOGGING
logger = logging.getLogger("nexus.gravity")

class GravityEngine:
    """
    Layer 1 Security: The Physics Check.
    Calculates the 'Semantic Weight' of a prompt.
    High Weight = High Entropy (Chaos/Violence).
    """
    
    def __init__(self):
        self.model = None
        self.dark_anchors = None
        self.anchor_embeddings = None
        self.has_vectors = False
        
        if HAS_VECTORS:
            logger.info("🌌 GRAVITY: Loading Local Embedding Model (all-MiniLM-L6-v2)...")
            try:
                # Load a tiny, fast model
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                
                # Define the "Dark Star" - concepts we want to measure distance TO.
                # If input is close to these, it has High Gravity.
                self.dark_anchors = [
                    "hate speech", "kill", "destroy", "murder", 
                    "torture", "self-harm", "illegal acts", 
                    "sexual violence", "humiliation", "slave"
                ]
                
                # Pre-calculate anchor embeddings
                self.anchor_embeddings = self.model.encode(self.dark_anchors, convert_to_tensor=True)
                logger.info("🌌 GRAVITY: Physics Engine Online.")
                self.has_vectors = True
            except Exception as e:
                logger.error(f"🌌 GRAVITY: Model Load Failed. Defaulting to Inertia. {e}")
                # Note: We don't change the global HAS_VECTORS here, but self.model will remain None
        else:
            logger.warning("🌌 GRAVITY: sentence-transformers not found. Running in Inertia Mode.")

    def calculate_weight(self, text: str) -> float:
        """
        Returns a float between 0.0 (Light/Safe) and 1.0 (Heavy/Dangerous).
        """
        if not HAS_VECTORS or not self.model:
            return 0.0 # Fail open (let the LLM Gate handle it)
            
        try:
            # Encode user text
            user_embedding = self.model.encode(text, convert_to_tensor=True)
            
            # Calculate cosine similarities to all Dark Anchors
            cosine_scores = util.cos_sim(user_embedding, self.anchor_embeddings)
            
            # The 'Weight' is the maximum similarity found
            # (i.e., how close is it to the WORST thing?)
            max_score = float(cosine_scores.max())
            
            # Normalize: Cosine is -1 to 1. We map meaningful positive correlation.
            # Usually > 0.3 is suspicious, > 0.6 is blatant.
            # We clamp to 0-1 range.
            weight = max(0.0, min(1.0, max_score))
            
            return weight
            
        except Exception as e:
            logger.error(f"Gravity Calculation Error: {e}")
            return 0.0

# Singleton Instance
@lru_cache()
def get_gravity_engine():
    return GravityEngine()
