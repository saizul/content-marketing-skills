# Newsletter formats

## Anatomy of an issue

1. **Opener** (1-3 sentences): what happened, why you are writing today. Personal.
2. **Main piece**: the one idea, how-to, story or case study. 150-600 words.
3. **Extras** (optional): 2-4 curated links with one line each on why they matter.
4. **One primary CTA**: a button or a clearly worded link. Secondary links are fine; a
   second CTA competing for the same click is not.
5. **Reply prompt**: a specific question. Replies build the relationship and help
   deliverability.
6. **Sign-off** with a name, not a company.
7. **Footer** (usually added by the platform): why they get this, unsubscribe, postal address.

## Formats

| Format | Best for | Shape |
| --- | --- | --- |
| One big idea | founders, consultants | opener / idea with example / what to do / CTA |
| How-to | freelancers, agencies teaching | problem / 3-5 steps / template link / CTA |
| Case study | agencies, B2B | client type / before / what changed / numbers / offer |
| Curated links | busy niche audiences | opener / 3-5 links with a take each / CTA |
| Founder update | early customers, investors | what shipped / what we learned / what is next / ask |
| Repurposed post | blog-driven lists | why this post now / 3 takeaways / read more |

## Tone and length

- Write to one reader. "You", not "you all" or "our subscribers".
- 200-600 words for most issues; long issues are fine when the list expects them, but put
  the main point in the first screen.
- Link text says where it goes: "the brief template", not "here".
- Images: always alt text, never put the key message only in an image (often blocked).

## Merge tags

- Liquid-style platforms (for example Kit and beehiiv) use `{{ ... }}` tags, usually with a
  `default` filter for the fallback.
- Mailchimp uses `*|FNAME|*`; set the default value in the audience field settings.
- Exact variable names differ between platforms and change over time: copy them from the
  platform's personalisation menu, then send a test to a contact without a first name.
