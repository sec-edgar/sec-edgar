# Test fixtures — synthetic data, not SEC data

**Every number in this directory is invented.** These files exist so the test
suite runs with no network access. They imitate the *shape* of SEC EDGAR
responses; they do not contain real figures for any real company.

The companies in these fixtures are fictional and were chosen so that nobody
can mistake a fixture for a result:

| Fixture company | Ticker | CIK | Why it exists |
|---|---|---|---|
| Testco Industries Inc | TSTC | 9999901 | The happy path: reports the preferred revenue tag |
| Fallback Systems Corp | FBSY | 9999902 | Does not report the preferred tag; exercises the fallback chain |
| Restated Metals Inc | RSTD | 9999903 | Reports one period twice with different values |
| Aperture Science Inc | APRT | 9999904 | Ambiguity: name collides with the next row |
| Aperture Holdings Corp | APHC | 9999905 | Ambiguity: name collides with the previous row |

Fixture values are deliberately round and implausible (111,000,000,000 and
similar) so that if one ever leaks into a document it is obviously not a real
reported figure.

If you want to check this code against real SEC data, run the tools against the
live API — see the "Run it yourself" section of the top-level README. The unit
tests will never do that.
