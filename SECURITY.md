# Security Policy

## Supported versions

| Version | Supported |
| --- | --- |
| 0.1.x | yes |

## What counts as a vulnerability

These skills are run by AI agents on real client content, so unsafe behaviour is
treated like a code vulnerability:

- A script that makes network calls, writes outside the output path it was given, or
  overwrites a file without `--force`
- Code or command injection: a crafted Markdown, HTML or CSV file that makes a script
  execute something or read files it was not given
- A `SKILL.md` workflow that tells the agent to publish, post, send, schedule, redirect or
  delete anything without asking the user first, or to request account passwords or API keys
- Guidance that leads the agent to fabricate data, testimonials or results presented as real
- Advice that is wrong in a way that harms users, e.g. a compliance note that would make
  marketing email unlawful

A check that misses a problem (false negative) is a normal bug: please open an issue.

## Reporting

Please **do not** open a public issue. Use
[GitHub private vulnerability reporting](https://github.com/saizul/content-marketing-skills/security/advisories/new)
with the affected skill, version, impact and steps to reproduce. Remove client content,
subscriber data and real URLs from examples.

You will get an answer within 5 working days. Fixes are released as soon as possible and
credited in the changelog unless you prefer otherwise.
