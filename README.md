# bytechef-automation-sample-code-workflow-python

A sample ByteChef **automation code project** written in Python. The whole project is one file,
[`src/sample_code_project.py`](src/sample_code_project.py), and that file is what you deploy - there is no build step.
The file is a single Python script. The server runs it with GraalPy and reads the value of its **last expression**: the
script defines each task's `perform` function with `def`, builds the project as a plain `dict` assigned to `project`,
and ends with `project` alone on the last line. The server reads the dict's `name`, `description`, `version` and
`workflows`, then calls each task's `perform(input, context)` when the workflow runs. Keep the definition a plain dict
and keep it last: anything after it, or a `main()` wrapper, hides the dict from the server.

The project, "Sample Code Project Python", has five workflows:

- `sampleWorkflow1` takes a `name` input, runs one task, `greet`, that logs and returns `Hello, <name>!`, and exposes
  that as the `greeting` output.
- `summarizeNewEmail` starts with the Gmail **New Email** polling trigger (`googleMail/v1/newEmailPolling`). It runs
  once for every new email and returns a one-line summary as the `summary` output.
- `fetchRecentEmails` takes an optional `from` input, calls the Gmail **Search Email** action and returns the matching
  messages as the `emails` output.
- `notifySlackOnNewEmail` starts with the Gmail **New Email** trigger and takes a required `channel` input; its options
  come from Slack's own `channel` input (`componentName`, `componentVersion` and `groupName` on the input), so it is
  picked from the Slack workspace's channels. Its `postToSlack` task calls the Slack **Send Channel Message** action, so
  it declares a `slack` connection and passes its name: pick a Slack connection for it in the test configuration or when
  deploying the project.
- `listOrders` starts with the API Platform **New API Request** trigger (`apiPlatform/v1/newApiRequest`), so it can back
  an API Platform endpoint. Its `fetchOrders` task returns a list of orders, and its `respond` task is a component task
  that runs the API Platform **Response to API Request** action with the `fetchOrders` output as the response body.

### Component tasks

A task that only runs a component action, with no logic of its own, can name the action by type instead of declaring
a `perform` function, the same way a trigger names its component:

```python
{
    "name": "respond",
    "type": "apiPlatform/v1/responseToAPIRequest",
    "parameters": {"responseType": "SUCCESS", "response": {"success": "${fetchOrders}"}},
}
```

The type is `<component>/v<version>/<action>`, and `parameters` holds the action's inputs. A `${...}` expression is
evaluated when the task runs: `"${fetchOrders}"` is the whole output of the `fetchOrders` task, `"${fetchOrders.count}"`
one of its fields and `"${fetchOrders.orders[0].id}"` an element of a list, and text such as
`"Found ${fetchOrders.count} orders"` becomes a string with the value filled in. Python's own f-strings use `{...}`
without the `$`, so a `${...}` in a plain string literal is left for the platform. A component task declares no
`connections`: when its action needs one, the workflow's test configuration and the project deployment ask for it like
for the same task in a visual workflow. Deploying fails when the component, its version or the action does not exist on
the server.

To serve `listOrders`, create an API collection for the deployed project under Automation → **API Platform**, add an
endpoint that runs `listOrders`, and enable both; a request to the endpoint answers with the orders.

### Connections

A task names the connections it uses and calls a component action through one of them:

```python
def fetch_emails(input: Dict[str, Any], context: "TaskContext") -> Any:
    return context.component.googleMail.searchEmail({"maxResults": 10}, "gmail")

# in the task definition:
"connections": [{"componentName": "googleMail", "name": "gmail"}],
"perform": fetch_emails,
```

The declared connection, and the Gmail trigger, show up in the workflow's test configuration and in the project
deployment like any other workflow connection: pick a Gmail connection for `gmail` there. Nothing in the source names a
specific account.

A task's `perform` takes `(input, context)`. `input` is a dict of the workflow inputs plus the output of every task that
already ran (under the task's name), so `input.get("name")` returns one of them, and `context.log(level, message)`
writes to the execution log. A task that reads its connections' parameters, to build a request itself, declares a third
parameter and takes `perform(input, connection, context)` instead: `connection` maps each declared connection's name to
that connection's parameters, credentials included.

## Types

The keys are the same camelCase keys as in a JavaScript code project. To have a type checker catch a missing `name` or a
misspelled `perform`, the file is annotated with the types from the
[`bytechef-workflow-api`](https://pypi.org/project/bytechef-workflow-api/) package: `project: "ProjectDefinition"` and
`def greet(input: Dict[str, Any], context: "TaskContext") -> str`. The ByteChef runtime can't import that package, so
the file imports it only under `typing.TYPE_CHECKING` and quotes the annotations; at run time the import is skipped.
Standard-library imports are fine; nothing else is available on the server.

## Check

```bash
python3 scripts/check.py src/sample_code_project.py name=Ada
```

Evaluates the file the same way the server does (runs every statement but the last, then evaluates the last
expression), checks its shape and runs each task once with a stub context. The stub stands in for Gmail: every trigger
output and every component action call returns a fixed sample email, and a request trigger an empty body. A component
task prints its action type and its parameters with the `${...}` expressions filled in. It needs
only Python 3.9 or later; there are no dependencies to install.

To type check the file as well:

```bash
pip install -r requirements-dev.txt
mypy --strict src scripts
```

`requirements-dev.txt` installs `bytechef-workflow-api` and `mypy`.

## Deploy

Upload `src/sample_code_project.py`. Deploying a project with the same name again deploys a new version of that
project instead of creating a second one.

### From the UI

Automation → **Projects** → the arrow next to **New Project** → **Import Code Project**, then pick the file.

### Through the public API

`POST /api/automation/v1/projects/deploy` with a `multipart/form-data` body:

| Part | Value |
|------|-------|
| `workspaceId` (query parameter) | The workspace the project belongs to. Send it - the upload fails without it. |
| `projectFile` (file part) | The `.py` file. The file name must end in `.py`; the server picks the language from the extension. |

Authenticate with `Authorization: Bearer <API key>`, using a workspace API key (Settings → Current Workspace →
**API Keys**) that belongs to an administrator - deploying requires the admin role. The key is looked up in the
environment named by the `X-ENVIRONMENT` header (`DEVELOPMENT`, `STAGING` or `PRODUCTION`; `PRODUCTION` when the
header is absent), so send the environment the key was created in. A successful deploy returns `204 No Content`.

```bash
curl -X POST "$BYTECHEF_URL/api/automation/v1/projects/deploy?workspaceId=1" \
  -H "Authorization: Bearer $BYTECHEF_API_KEY" \
  -H "X-ENVIRONMENT: DEVELOPMENT" \
  -F "projectFile=@src/sample_code_project.py"
```

`BYTECHEF_URL` is the server's base URL, for example `http://localhost:9555` for a local development server.
