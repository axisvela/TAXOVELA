# Example 07 — Core Banking / Payments (PENDING INPUT)

Placeholder for the finance example: core banking / payment system on
private cloud with a two-site-three-center DR topology, Restricted data
classification, and strong authentication.

**Status**: waiting for the reference diagram / requirements input.
Once the original reference image is available, place it under
`input/diagrams/` and derive `input/prompt.md` and
`input/documents/requirements.md` following the pattern of examples 01–06.

Planned highlights:

- Two-site-three-center (same-city active-active + remote DR)
- Acme Restricted data: AES-256 at rest, TLS 1.3 in transit
- Strong customer authentication (MFA) + anti-fraud integration
- No internet-facing surface except via F5 → DMZ
