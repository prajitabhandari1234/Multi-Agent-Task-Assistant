# Import Any and Dict so message content can contain
# different types of structured information
from typing import Any, Dict

# BaseModel provides validation for agent messages
# Field allows us to create safe default dictionary values
from pydantic import BaseModel, Field


# Represents a structured message exchanged between agents
class AgentMessage(BaseModel):

    # Name of the agent sending the message
    sender: str

    # Name of the agent that should receive the message
    receiver: str

    # Describes what the receiving agent is expected to do
    intent: str

    # Stores the main structured information carried by the message
    content: Dict[str, Any]

    # Stores optional rules or restrictions for processing the message
    constraints: Dict[str, Any] = Field(default_factory=dict)