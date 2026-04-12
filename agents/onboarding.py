"""
Onboarding agent — collects user profile via conversation.

Uses a save_profile ADK tool so the agent can persist the profile
to SQLite once all information has been gathered and confirmed.
"""

from db import database
from agents.base import WorkoutAgent


def save_profile(
    name: str,
    age: int,
    height_cm: float,
    weight_kg: float,
    goals: str,
    gym_frequency: str,
    experience_level: str,
    injuries: str = "none",
    diet_prefs: str = "none",
) -> str:
    """
    Save the user's fitness profile to the database.
    Call this once the user has confirmed all their details are correct.

    Args:
        name: User's first name.
        age: Age in years.
        height_cm: Height in centimetres.
        weight_kg: Weight in kilograms.
        goals: Fitness goals (comma-separated if multiple, e.g. "lose fat, build muscle").
        gym_frequency: How often they currently work out (e.g. "3x per week").
        experience_level: One of: beginner, intermediate, advanced.
        injuries: Any injuries or physical limitations, or "none".
        diet_prefs: Dietary preferences/restrictions, or "none".

    Returns:
        Confirmation message to relay to the user.
    """
    database.save_profile(
        {
            "name": name,
            "age": age,
            "height_cm": height_cm,
            "weight_kg": weight_kg,
            "goals": goals,
            "gym_frequency": gym_frequency,
            "experience_level": experience_level,
            "injuries": injuries,
            "diet_prefs": diet_prefs,
        }
    )
    return "Profile saved successfully."


agent = WorkoutAgent(
    name="onboarding_agent",
    prompt_file="onboarding.txt",
    tools=[save_profile],
)
