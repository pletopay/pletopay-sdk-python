# Security

Please report vulnerabilities in this SDK or in the Pletopay API privately to security@pletopay.com. Do not open a public issue. We acknowledge reports within two business days.

## Using the SDK safely

- Keep secret keys (`sk_…`) on the server and out of source control. Browsers only ever see publishable keys (`pk_…`) with pletopay.js; this SDK refuses them.
- Verify every webhook with `construct_event` against the raw request body before acting on it, and de-duplicate on the event id.
- Pass deterministic idempotency keys for transfers and refunds so retries cannot move money twice.
- Keep the package up to date; releases are published to PyPI from this repository's release workflow with trusted publishing.
