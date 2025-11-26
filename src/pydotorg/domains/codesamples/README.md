# Code Samples Domain

Domain for managing Python code samples and examples.

## Models

- **CodeSample**: Code snippets with descriptions for demonstrating Python features

## API Endpoints

- `GET /api/v1/code-samples` - List all code samples
- `GET /api/v1/code-samples/{sample_id}` - Get code sample by ID
- `GET /api/v1/code-samples/slug/{slug}` - Get code sample by slug
- `GET /api/v1/code-samples/published` - List published code samples
- `POST /api/v1/code-samples` - Create new code sample
- `PUT /api/v1/code-samples/{sample_id}` - Update code sample
- `DELETE /api/v1/code-samples/{sample_id}` - Delete code sample
