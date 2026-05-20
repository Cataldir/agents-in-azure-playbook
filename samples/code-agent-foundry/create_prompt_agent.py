"""Optional Foundry SDK sample for the Code Agents architecture label.

Code Agents is a sample label in this repository, not an official Foundry agent
type. The official product concept demonstrated here is a prompt agent created
through the Foundry SDK boundary.
"""

from __future__ import annotations

import os
import sys


def main() -> int:
    """Create and invoke a prompt agent when SDK packages and config exist."""

    project_endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
    model_deployment = os.getenv("AZURE_AI_MODEL_DEPLOYMENT")
    agent_name = os.getenv("FOUNDRY_AGENT_NAME", "agents-in-azure-playbook-demo")

    if not project_endpoint or not model_deployment:
        print(
            "Set AZURE_AI_PROJECT_ENDPOINT and AZURE_AI_MODEL_DEPLOYMENT before "
            "running this optional sample."
        )
        return 2

    try:
        from azure.ai.projects import AIProjectClient
        from azure.ai.projects.models import PromptAgentDefinition
        from azure.identity import DefaultAzureCredential
    except ImportError:
        print("Install optional packages first: python -m pip install -e .[foundry]")
        return 2

    project_client = AIProjectClient(
        endpoint=project_endpoint,
        credential=DefaultAzureCredential(),
    )
    openai_client = project_client.get_openai_client()

    agent = project_client.agents.create_version(
        agent_name=agent_name,
        definition=PromptAgentDefinition(
            model=model_deployment,
            instructions=(
                "You are a concise architecture assistant. Explain the runtime "
                "boundary before naming product features."
            ),
        ),
    )

    response = openai_client.responses.create(
        input="Explain the difference between a prompt agent and custom runtime code.",
        extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
    )
    print(response.output_text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
