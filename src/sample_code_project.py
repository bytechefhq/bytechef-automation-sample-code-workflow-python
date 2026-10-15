from typing import TYPE_CHECKING, Any, List

if TYPE_CHECKING:
    from bytechef_workflow_api import ProjectDefinition, TaskContext


def greet(context: "TaskContext") -> str:
    name = context.input("name")

    context.log("info", f"Greeting {name}")

    return f"Hello, {name}!"


def summarize(context: "TaskContext") -> str:
    email = context.input("newEmail")

    summary = f"New email from {email['from']}: {email['subject']}"

    context.log("info", summary)

    return summary


def fetch_emails(context: "TaskContext") -> List[Any]:
    result = context.component.googleMail.searchEmail({"from": context.input().get("from"), "maxResults": 10}, "gmail")

    messages: List[Any] = result.get("messages") or []

    context.log("info", f"Found {len(messages)} emails")

    return messages


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
        },
        {
            "name": "summarizeNewEmail",
            "label": "Summarize New Email",
            "description": "Runs for every new email in the inbox and logs who sent it.",
            # The trigger runs on the Gmail connection chosen for it when the project is deployed.
            "triggers": [
                {"name": "newEmail", "type": "googleMail/v1/newEmailPolling", "parameters": {"format": "SIMPLE"}}
            ],
            "outputs": [{"name": "summary", "task": "summarize"}],
            "tasks": [
                {
                    "name": "summarize",
                    "label": "Summarize",
                    "perform": summarize,
                }
            ],
        },
        {
            "name": "fetchRecentEmails",
            "label": "Fetch Recent Emails",
            "description": "Returns the most recent emails, optionally only those from one sender.",
            "inputs": [{"name": "from", "label": "From", "type": "STRING", "required": False}],
            "outputs": [{"name": "emails", "task": "fetchEmails"}],
            "tasks": [
                {
                    "name": "fetchEmails",
                    "label": "Fetch Emails",
                    # A code task's perform calls actions itself, so it declares the connections it uses; the name is
                    # what perform passes to the action. Pick the Gmail connection for "gmail" in the test configuration
                    # or when deploying the project.
                    "connections": [{"componentName": "googleMail", "name": "gmail"}],
                    "perform": fetch_emails,
                }
            ],
        },
    ],
}

project
