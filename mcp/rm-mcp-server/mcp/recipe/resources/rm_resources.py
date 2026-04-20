from fastmcp.resources import resource
import logging

logger = logging.getLogger(__name__)


@resource(uri="recipe://docs/safety")
def get_safety_guidelines() -> str:
    """Mandatory kitchen safety protocols."""

    logger.debug("Fetching safety guidelines...")

    return """
    Safety Guidelines for Cooking:
    1. Always wash your hands before handling food.
    2. Keep raw and cooked foods separate to avoid cross-contamination.
    3. Cook foods to their recommended internal temperatures.
    4. Refrigerate perishable foods within two hours of cooking.
    5. Use clean utensils and surfaces when preparing food.
    """


@resource(uri="recipe://docs/measurements")
def get_measurements() -> str:
    """Common cooking measurements."""
    logger.debug("Fetching measurement conversions...")
    return """
    Measurement Conversions:
    1 cup = 16 tablespoons = 48 teaspoons = 240 ml
    1 tablespoon = 3 teaspoons = 14.8 ml
    1 teaspoon = 4.9 ml
    1 ounce = 28.3 grams
    1 pound = 454 grams
    """
