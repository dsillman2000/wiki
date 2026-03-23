# Issue: Implement `--random` flag for wiki CLI

## Overview

Add a `--random` flag to the `wiki` CLI tool that fetches a random Wikipedia article. The flag should work similarly to the existing `--search` flag but instead of searching, it fetches a random article.

## Requirements

### Core Functionality

1. **`--random` flag**: When specified, fetch a random Wikipedia article
2. **No section selection**: The `-s/--section` flag should be incompatible with `--random` (raise an error if both are used)
3. **Support `--ls`**: The `--list-sections` flag should work with `--random` to list sections of the random article
4. **Default output**: By default, return the full markdown content of the random article (same as normal article fetch)
5. **Support all output modes**: Should work with `--raw`, `-o/--output`, and Rich formatting

### API Integration

- Use the Wikipedia REST API endpoint: `https://en.wikipedia.org/api/rest_v1/page/random/summary`
- This endpoint returns a summary JSON similar to the regular summary endpoint
- Need to fetch full HTML content for sections using the title from the random summary

### User Experience

```
# Basic usage - get a random article
wiki --random

# Get random article with plain text output
wiki --random --raw

# Save random article to file
wiki --random -o random_article.md

# List sections of random article
wiki --random --ls

# Error: cannot combine --random with --section
wiki --random -s History  # Should raise error
```

## Implementation Plan

### 1. Add `--random` flag to CLI (`wiki_client/main.py`)

- Add `@click.option("--random", is_flag=True, help="Fetch a random Wikipedia article.")` decorator
- Add `random_mode: bool` parameter to `cli()` function
- Update `_run()` function to handle random mode
- Add validation: if `random_mode` and `section_filter` both True, raise `click.UsageError`

### 2. Add random article fetching to API (`wiki_client/api.py`)

- Add `fetch_random_article()` function:
  - Call `https://en.wikipedia.org/api/rest_v1/page/random/summary`
  - Get title from response
  - Fetch full HTML using existing `_fetch_html()` function
  - Parse sections using existing `_parse_sections()` and `_build_section_tree()`
  - Return same dict structure as `fetch_article()`
- Update `fetch_article()` to handle random mode? Or keep separate?

### 3. Update CLI logic (`wiki_client/main.py`)

- In `_run()` function, add branch for `random_mode`:
  - Call `api.fetch_random_article()`
  - Handle `--ls` and normal rendering similar to regular article flow
  - Use existing `render.render_article()` for display

### 4. Add tests (`tests/test_api.py`, `tests/test_render.py`)

- Add tests for `fetch_random_article()` function
- Mock HTTP responses for random endpoint
- Test CLI integration with `--random` flag
- Test error case when `--random` and `-s` are used together
- Test compatibility with `--ls`, `--raw`, `-o`

### 5. Update documentation

- Update `AGENTS.md` with new `--random` flag documentation
- Update CLI help text
- Add examples to docstring

## Technical Details

### Random API Endpoint

```
GET https://en.wikipedia.org/api/rest_v1/page/random/summary
```

Returns:

```json
{
  "title": "Article Title",
  "description": "Short description",
  "extract": "Lead paragraph",
  "content_urls": {
    "desktop": {
      "page": "https://en.wikipedia.org/wiki/Article_Title"
    }
  }
  // ... other summary fields
}
```

### Integration with Existing Code

The random article fetching should reuse existing infrastructure:

- `_fetch_html()` for full content
- `_parse_sections()` for section parsing
- `_build_section_tree()` for hierarchical sections
- `render_article()` for display

### Error Handling

- Network errors should be caught and displayed as `click.ClickException`
- If random fetch fails (HTTP error), show appropriate error message
- Validate incompatible flag combinations before making API calls

## Example Implementation

### API Function

```python
def fetch_random_article() -> dict:
    """Fetch a random Wikipedia article.

    Returns:
        Full article dict with title, description, sections, etc.

    Raises:
        httpx.HTTPStatusError: On HTTP errors.
        httpx.RequestError: On network failures.
    """
    # Fetch random summary
    with httpx.Client(headers={"User-Agent": USER_AGENT}, follow_redirects=True) as client:
        response = client.get("https://en.wikipedia.org/api/rest_v1/page/random/summary")
        response.raise_for_status()
        summary = response.json()

    # Fetch full HTML using title from summary
    canonical_title = summary.get("title", "")
    try:
        html = _fetch_html(canonical_title)
        flat = _parse_sections(html)
        section_tree = _build_section_tree(flat)
    except (httpx.HTTPStatusError, httpx.RequestError):
        section_tree = []

    return {**summary, "sections": section_tree}
```

### CLI Integration

```python
@click.option(
    "--random",
    is_flag=True,
    help="Fetch a random Wikipedia article.",
)
def cli(
    query: tuple[str, ...],
    search_mode: bool,
    raw: bool,
    list_sections: bool,
    section_filter: tuple[str, ...],
    output: str | None,
    random_mode: bool,  # New parameter
) -> None:
    # Validate incompatible flags
    if random_mode and section_filter:
        raise click.UsageError("--random cannot be used with --section/-s")

    if random_mode and query:
        raise click.UsageError("QUERY cannot be provided with --random")

    # In _run() function:
    if random_mode:
        data = api.fetch_random_article()
        # ... rest of rendering logic
```

## Testing Strategy

### Unit Tests

1. Test `fetch_random_article()` with mocked HTTP responses
2. Test CLI flag validation (--random + -s should error)
3. Test random mode with --ls, --raw, -o flags
4. Test that random article has expected structure (title, sections, etc.)

### Integration Tests

1. Test actual random fetch (optional, may be flaky)
2. Test output formatting matches regular article output

## Open Questions

1. Should `--random` accept a query? (Probably not - it's truly random)
2. Should there be a way to get multiple random articles? (Not in initial implementation)
3. Should random articles be cached? (No, fresh random each time)
4. What about language support? (Use English Wikipedia only for now)

## Success Criteria

1. `wiki --random` works and displays a random article
2. `wiki --random --ls` lists sections of random article
3. `wiki --random --raw` outputs plain text
4. `wiki --random -o file.md` saves to file
5. `wiki --random -s History` raises clear error
6. All existing tests still pass
7. Code follows project conventions (ruff, type hints, docstrings)

## Estimated Effort

- Implementation: 2-3 hours
- Testing: 1-2 hours
- Documentation: 30 minutes
- Total: 4-5 hours

Written by OpenCode.
