# Testing headlines for real

The script narrows the options; readers decide.

## SEO title tags (Search Console)

There is no built-in A/B split for organic results on one URL, so test sequentially:

1. Pick pages with steady impressions (1,000+ per 28 days) and a stable average position.
2. Record 28 days of clicks, impressions, CTR and position for the page (Search Console >
   Performance > filter by page).
3. Change only the title tag (and nothing else on the page). Note the date.
4. Wait for Google to recrawl (URL Inspection shows the last crawl), then compare the next
   28 days with the previous 28 at similar average position.
5. Keep the winner if CTR improved without a position drop; otherwise revert.

Google may show a different title than your title tag. If the shown title differs, the
test measures Google's rewrite, not yours; check the live result.

Sites with many similar pages (product, location, template pages) can split pages into
control and test groups and compare the groups over the same dates.

## Email subject lines

Most email platforms have a built-in A/B test (subject line variants):

- Test one variable (the subject), same send time and content.
- Use a sample large enough to matter: with small lists (under ~2,000), the result is
  mostly noise; test the same hypothesis over several sends instead.
- Opens are inflated by privacy features such as Apple Mail Privacy Protection; prefer
  clicks or replies as the deciding metric.

## Social hooks

- Post the same idea with different hooks a week or more apart, or use the losing hook
  later as a reshare.
- Compare impressions-normalised engagement (comments and reposts per 1,000 impressions),
  not raw likes.

## Record keeping

Keep a simple log: date, page or campaign, variant A, variant B, metric, result, decision.
Patterns across tests (numbers win, questions lose for this audience) matter more than any
single result.
