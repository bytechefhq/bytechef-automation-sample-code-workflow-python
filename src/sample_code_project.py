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


def post_to_slack(context: "TaskContext") -> Any:
    email = context.input("newEmail")

    text = f"New email from {email['from']}: {email['subject']}"

    message = context.component.slack.sendChannelMessage({"channel": context.input("channel"), "text": text}, "slack")

    context.log("info", f"Posted to Slack: {text}")

    return message


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
        {
            "name": "notifySlackOnNewEmail",
            "label": "Notify Slack on New Email",
            "description": "Posts every new email in the inbox to a Slack channel.",
            "inputs": [{"name": "channel", "label": "Slack Channel ID", "type": "STRING", "required": True}],
            "triggers": [
                {"name": "newEmail", "type": "googleMail/v1/newEmailPolling", "parameters": {"format": "SIMPLE"}}
            ],
            "outputs": [{"name": "message", "task": "postToSlack"}],
            "tasks": [
                {
                    "name": "postToSlack",
                    "label": "Post to Slack",
                    "description": "Posts the sender and subject with the Slack Send Channel Message action.",
                    # The Gmail trigger needs no declaration, but the task calls Slack itself, so it declares
                    # that connection and passes the name. Pick the Slack connection for "slack" in the test
                    # configuration or when deploying the project.
                    "connections": [{"componentName": "slack", "name": "slack"}],
                    "perform": post_to_slack,
                }
            ],
        },
    ],
}

project
