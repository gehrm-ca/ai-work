# Verdict Forecast — read-only source adapters (review branch)

This is an **isolated experiment**. The repository's original Program OS product is unchanged. The fuller founder demo, with local SQLite forecast ledger, lock approval gates, resolution workflow and UI, is packaged separately as `Verdict_Forecast_Adversarial_V8_Pack.zip` in the ChatGPT conversation.

The adapters in this PR cover public metadata only: Macro Voices RSS, Kalshi market list, Polymarket Gamma list and BLS unemployment series. They do **not** authenticate a voice or video, verify statements, permit commercial redistribution, place trades or match prediction-market contracts to speakers' propositions. Do not show these markets in published graphics without reviewing market rules and redistribution rights.

Run `python -m unittest discover -s experiments/verdict-forecast -p 'test_*.py' -v` from repo root. Standard library only; tests use mocked HTTP responses and need no internet.

## Source provenance rule
A content credential, podcast link or file hash is a provenance/integrity signal, **not proof that the content is real or true**. The commercial product requires publisher-held original, exact speaker-confirmed quote and probability, source custody, human editor approval and independent evidence for outcome resolution.

## Source references
- https://www.macrovoices.com/ (transcript links)
- https://feed.podbean.com/macrovoices/feed.xml (public podcast RSS)
- https://docs.kalshi.com/api-reference/market/get-markets
- https://docs.polymarket.com/
- https://www.bls.gov/developers/
- https://contentauthenticity.org/how-it-works

## Before integrating into a product
Get publisher media rights and data licenses, dedicated repo, external audit anchoring, test corpus with deepfakes and source revisions, authentication, multi-tenant security, human review and correction policy. This is not production software.
