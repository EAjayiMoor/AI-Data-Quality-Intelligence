# Security and Data

## Data policy
- Use synthetic data only.
- Do not copy client notes, identifiers, screenshots or schemas.
- Label the interface and exports as synthetic demonstration data.

## Secrets
- Store API keys and connection strings in environment variables locally.
- Use an approved secret store for a shared deployment.
- Commit only `.env.example` with placeholders.

## Database access
- Application account receives only required permissions.
- The LLM has no direct database credentials.
- Source tables are not updated by model output.

## LLM boundary
- Send only the selected request's required fields.
- Avoid unnecessary personal or customer data, even when synthetic.
- Do not log provider credentials or full prompts in standard application logs.
- Record prompt version and usage metadata.

## Application controls
- Validate all structured model output.
- Parameterise SQL queries.
- Escape or safely render note content.
- Apply context-size limits.
- Surface truncation as an exception.

## Demo disclaimer
The PoC supports exploration and assurance. It does not make operational decisions and is not presented as production-ready.
