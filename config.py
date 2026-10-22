"""Settings shared by the whole shell."""
import os

# LLM model used by the router and by every agent.
# Change it without editing code:  export HUNTER_MODEL="another-model-name"
MODEL = os.environ.get("HUNTER_MODEL", "claude-sonnet-5-5")

# Maximum LLM calls for one user request (stops endless loops).
MAX_STEPS = 8


def make_client():
    """Create the Anthropic client. Needs ANTHROPIC_API_KEY in the environment."""
    import anthropic
    return anthropic.Anthropic()
