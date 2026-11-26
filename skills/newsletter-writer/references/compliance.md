# Compliance basics (not legal advice)

Rules depend on where you and your subscribers are. Confirm with your email platform's
documentation and, for anything unusual, a lawyer.

## United States: CAN-SPAM Act (FTC)

- No false or misleading header information or deceptive subject lines.
- Identify the message as an ad where it is one.
- Include a valid physical postal address.
- Provide a clear way to opt out, and honour opt-outs within 10 business days.

## EU / UK: GDPR and ePrivacy / PECR

- Marketing email generally needs prior consent (with a limited "soft opt-in" for existing
  customers in the UK and some EU countries).
- Keep a record of when and how each subscriber consented.
- Every message needs an easy unsubscribe.

## Mailbox provider requirements (Gmail and Yahoo, since 2024)

Bulk senders (Gmail defines this as roughly 5,000+ messages a day to its users) must
authenticate mail (SPF, DKIM, DMARC), support one-click unsubscribe (RFC 8058 List-Unsubscribe
headers) and keep spam complaint rates low (Google's threshold is 0.3%). Most newsletter
platforms handle the headers; you handle consent and content.

## What the checker can and cannot see

- `compliance.unsubscribe` only looks for an unsubscribe link, merge tag or "manage
  preferences" text in your draft. If your platform adds the footer automatically, the
  finding is expected: confirm it in a test send.
- It cannot check consent, the postal address in the platform footer or authentication.
