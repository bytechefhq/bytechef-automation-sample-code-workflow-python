from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bytechef_workflow_api import ProjectDefinition, TaskContext


def greet(context: "TaskContext") -> str:
    name = context.input("name")

    context.log("info", f"Greeting {name}")

    return f"Hello, {name}!"


project: "ProjectDefinition" = {
    "name": "Sample Code Project Python",
    "version": "1",
    "description": "Sample code project description.",
    "workflows": [
        {
            "name": "sampleWorkflow1",
            "label": "Sample workflow 1",
            "description": "Greets the name it is given.",
            "inputs": [{"name": "name", "label": "Name", "type": "STRING", "required": True}],
            "outputs": [{"name": "greeting", "task": "greet"}],
            "tasks": [
                {
                    "name": "greet",
                    "label": "Greet",
                    "description": "Builds a greeting from the name input.",
                    "perform": greet,
                }
            ],
        }
    ],
}

project
