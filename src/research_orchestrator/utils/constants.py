"""Centralized constants for the research orchestrator."""


class Models:
    """Claude model identifiers."""
    SONNET_4 = "claude-sonnet-4-20250514"
    HAIKU_4 = "claude-haiku-4-20250514"
    OPUS_4 = "claude-opus-4-20250514"

    # Semantic aliases
    DEFAULT = HAIKU_4
    HIGH_QUALITY = SONNET_4
    FAST = HAIKU_4

    @classmethod
    def get_pricing(cls, model: str) -> tuple[float, float]:
        """Return (input_price_per_M, output_price_per_M) for model."""
        pricing = {
            cls.HAIKU_4: (0.25, 1.25),
            cls.SONNET_4: (3.0, 15.0),
            cls.OPUS_4: (15.0, 75.0),
        }
        return pricing.get(model, (3.0, 15.0))  # Default to Sonnet pricing
