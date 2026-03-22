# Feature Request: Proper Code Block, Quote, and Link Rendering

## Problem Statement

The current rendering implementation strips all HTML formatting during content extraction, resulting in plain text output that loses important structural and formatting information. Code blocks, inline code, and quotation blocks are not being properly detected or rendered.

## Current Behavior

When fetching an article like "Python (programming language)" and viewing the "Function syntax" section:

```
$ uvx --from wiki-client wiki "Python (programming language)" -s Function

Function syntax

Functions are created in Python by using the def keyword. A function is defined similarly to how it is called, by first providing the function name and
then the required parameters. Here is an example of a function that prints its inputs: def printer ( input1 , input2 = "already there" ): print ( input1 )
print ( input2 ) printer ( "hello" ) # Example output: # hello # already there To assign a default value to a function parameter in case no actual value is
provided at run time, variable-definition syntax can be used inside the function header.
```

**Issues observed:**

1. Code blocks are rendered as inline plain text with spaces removed
2. Python syntax highlighting spans (`<span class="k">`, `<span class="nf">`, etc.) are stripped
3. Comments (`#`) appear inline without code block formatting
4. The code structure is difficult to read
5. Wikipedia links to other articles are indistinguishable from regular text
6. No visual indication that certain terms link to other articles on Wikipedia

## Expected Behavior

The same section should render code blocks with proper formatting:

````markdown
## Function syntax

Functions are created in Python by using the `def` keyword. A function is defined
similarly to how it is called...

```python
def printer(input1, input2="already there"):
    print(input1)
    print(input2)

printer("hello")

# Example output:
# hello
# already there
```
````

To assign a default value to a function parameter in case no actual value is
provided at run time, variable-definition syntax can be used inside the function header.

````

## Root Cause Analysis

In `wiki_client/api.py`, the `_make_entry` function extracts content as plain text:

```python
content = re.sub(r"\s+", " ", entry_soup.get_text(separator=" ")).strip()
````

This approach:

1. Uses `get_text()` which strips all HTML tags
2. Converts all whitespace to single spaces
3. Destroys structural elements like `<pre>`, `<blockquote>`, `<code>`

### Wikipedia HTML Structure

Wikipedia's REST API returns code blocks in this format:

```html
<div
  class="mw-highlight mw-highlight-lang-python mw-content-ltr"
  dir="ltr"
  typeof="mw:Extension/syntaxhighlight"
  data-mw='{"name":"syntaxhighlight","attrs":{"lang":"python"},"body":{"extsrc":"def foo():\n    pass\n"}}'
>
  <pre>
    <span class="k">def</span> <span class="nf">foo</span><span class="p">():</span>
    <span class="w"></span><span class="k">pass</span>
  </pre>
</div>
```

Key elements:

- `<div class="mw-highlight">` - wrapper with language class
- `<pre>` - the code block container
- `data-mw.body.extsrc` - raw source code
- `<span class="...">` - syntax highlighting spans

Inline code uses `<code class="mw-highlight">` elements.

## Missing Features

### 1. Code Block Detection and Rendering

- [ ] Detect `<pre>` tags or `<div class="mw-highlight">` elements
- [ ] Extract code from `data-mw.body.extsrc` or `<pre>` text content
- [ ] Wrap code in triple backticks with language identifier for Markdown
- [ ] Handle multiline code blocks properly (preserve line breaks)

### 2. Inline Code Detection

- [ ] Detect `<code>` tags (excluding those inside `<pre>` blocks)
- [ ] Wrap inline code in single backticks

### 3. Quote Block Rendering

- [ ] Detect `<blockquote>` elements
- [ ] Render as Markdown blockquotes (`> text`)
- [ ] Handle nested quotes properly

### 4. Syntax Highlighting (Optional Enhancement)

- [ ] Consider using Rich's `Syntax` class for colored terminal output
- [ ] Extract language from `mw-highlight-lang-*` classes
- [ ] Strip span-based highlighting when using plain Markdown

### 5. Wikipedia Link Styling

Currently, links to other Wikipedia articles are stripped entirely during HTML parsing. Users cannot identify which text portions are clickable links to other articles.

**Wikipedia HTML Structure:**

```html
<!-- Internal wiki links -->
<a
  rel="mw:WikiLink"
  href="./Object-oriented_programming"
  title="Object-oriented programming"
  >object-oriented</a
>

<!-- External links -->
<a rel="mw:ExtLink" href="https://python.org" class="external text"
  >python.org</a
>
```

**Current behavior:**

```
...supports multiple programming paradigms, including structured (particularly procedural), object-oriented and functional programming.
```

**Expected behavior (Rich-styled links):**

```
...supports multiple programming paradigms, including structured (particularly procedural), [object-oriented] and functional programming.
```

Where `[object-oriented]` would be styled distinctly (e.g., cyan color, underline) to indicate it's a clickable link.

- [ ] Detect `<a rel="mw:WikiLink">` elements
- [ ] Preserve link text while styling with Rich
- [ ] Consider including the target article name for clarity (e.g., `[object-oriented][1]` or similar)
- [ ] Handle external links (`<a rel="mw:ExtLink">`) distinctly from internal wiki links
- [ ] For raw/Markdown output, convert to Markdown link syntax `[text](url)`

## Proposed Implementation Approach

### Option A: Enhanced HTML Parsing

Modify `_make_entry` in `api.py` to:

1. First extract and preserve code blocks, converting them to Markdown code fences
2. Then extract remaining content with proper whitespace handling
3. Pass structured content (markdown + code blocks) to renderer

### Option B: Rich Syntax Integration

In `render.py`:

1. Detect code blocks in content string (markdown or custom markers)
2. Use Rich's `Syntax` class for code blocks
3. Use `Markdown` class for regular text with blockquotes

### Recommended: Hybrid Approach

1. **In `api.py`**: Convert Wikipedia HTML elements to Markdown during parsing:
   - `<pre>` / `<div class="mw-highlight">` → ``python`...``
   - `<code>` → `` `code` ``
   - `<blockquote>` → `> blockquote text`
   - `<a rel="mw:WikiLink">` → Markdown link `[text](wiki-url)` or styled text for Rich
   - `<a rel="mw:ExtLink">` → Markdown link `[text](url)` or styled text for Rich

2. **In `render.py`**: Use Rich's `Syntax` class for enhanced terminal rendering when available

## References

- Wikipedia REST API: https://en.wikipedia.org/api/rest_v1/
- Rich Documentation: https://rich.readthedocs.io/
- Markdown Code Fences: https://spec.commonmark.org/0.31.2/#code-fence

## Priority

**High** - Code blocks are essential for programming language articles, which are a primary use case for this CLI tool.
