# How to write docs with mkdocs

For full documentation visit [mkdocs.org](https://www.mkdocs.org).

## Basics

* `mkdocs serve` - Start the live-reloading docs server locally

Project layout:

    mkdocs.yml    # The configuration file.
    docs/
        index.md  # The documentation homepage.
        ...       # Other markdown pages, images and other files.

`MkDocs` are markdown documents, so the answer is easy: just use plain Markdown and, optionally, the supported extensions. More info [in the official docs](https://www.mkdocs.org/user-guide/writing-your-docs/#writing-with-markdown).

### Supported extensions

The theme we are using is `material`, which supports very fancy [extensions](https://squidfunk.github.io/mkdocs-material/extensions/admonition/).


#### Admonitions


!!! tip
    This is so cool huh? Check all styles [here](https://squidfunk.github.io/mkdocs-material/extensions/admonition/#types).

```md
!!! tip
    This is so cool huh? Check all styles [here](https://squidfunk.github.io/mkdocs-material/extensions/admonition/#types).

```

#### Citations

> This is a very important finding.[^1]

> This is yet another finding.[^Rodríguez-Guerra and Pedregal, 1990]

[^1]: Lorem ipsum dolor sit amet, consectetur adipiscing elit.

[^Rodríguez-Guerra and Pedregal, 1990]: A kid named Jaime.

These are written with labels like this:

```md
> This is a very important finding.[^1]

> This is yet another finding.[^Rodríguez-Guerra and Pedregal, 1990]

[^1]: Lorem ipsum dolor sit amet, consectetur adipiscing elit.

[^Rodríguez-Guerra and Pedregal, 1990]: A kid named Jaime.
```

#### LaTeX

Either in blocks

$$
\frac{n!}{k!(n-k)!} = \binom{n}{k} * Jaime
$$

```latex
$$
\frac{n!}{k!(n-k)!} = \binom{n}{k} * Jaime
$$
```

or inline:

> This my best equation ever: $p(x|y) = \frac{p(y|x)p(x)}{p(y)}$

```latex
This my best equation ever: $p(x|y) = \frac{p(y|x)p(x)}{p(y)}$
```

#### Checkboxes

- [ ] Checkbox
- [X] Checkbox

```
- [ ] Checkbox
- [X] Checkbox
```

#### Emoji

Github shortcuts are supported:

:smile: :heart: :thumbsup:

```
:smile: :heart: :thumbsup:
```

#### Tabbed fences

``` tab="Step 1"

This is the step 1
```

```python tab="Step 2"

# This is the step 2 with python code highlighting
he = Element("Helium")
```

``` tab="Step 3"

This is the step 3
```

This line interrupts the fences and creates a new block of tabs

```python tab="Step 4"

# This is the step 4 with python code highlighting
be = Element("Beryllium")
```

Obtained with:

    ``` tab="Step 1"

    This is the step 1
    ```

    ```python tab="Step 2"

    # This is the step 2 with python code highlighting
    he = Element("Helium")
    ```

    ``` tab="Step 3"

    This is the step 3
    ```

    This line interrupts the fences and creates a new block of tabs

    ```python tab="Step 4"

    # This is the step 4 with python code highlighting
    be = Element("Beryllium")
    ```

#### Extra inline markup

| Code      | Result  |
|-----------|---------|
| `==hey==` | ==hey== |
| `~~hey~~` | ~~hey~~ |
| `^^hey^^` | ^^hey^^ |
| `a^migo^` | a^migo^ |
| `-->`     | -->     |


### Docstrings

We are using [`mkdocstrings`](https://pawamoy.github.io/mkdocstrings/) for our docstrings, which deviate slightly from the more popular `numpydoc` syntax. Instead, it's closer to [Google-style docstrings](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html). To sum up, this is a more or less complete example of the requested syntax:

    """
    A short description of this function.

    A longer description of this function.
    You can use more lines.

        This is code block,
        as usual.

        ```python
        s = "This is a Python code block :)"
        ```

    Arguments:
        param1: An integer?
        param2: A string? If you have a long description,
            you can split it on multiple lines.
            Just remember to indent those lines with at least two more spaces.
            They will all be concatenated in one line, so do not try to
            use complex markup here.

    Note:
        We omitted the type hints next to the parameters names.
        Usually you would write something like `param1 (int): ...`,
        but `mkdocstrings` gets the type information from the signature, so it's not needed here.

    Exceptions are written the same.

    Raises:
        OSError: Explain when this error is thrown.
        RuntimeError: Explain as well.
            Multi-line description, etc.

    Let's see the return value section now.

    Returns:
        A description of the value that is returned.
        Again multiple lines are allowed. They will also be concatenated to one line,
        so do not use complex markup here.

    Note:
        Other words are supported:

        - `Args`, `Arguments`, `Params` and `Parameters` for the parameters.
        - `Raise`, `Raises`, `Except`, and `Exceptions` for exceptions.
        - `Return` or `Returns` for return value.

        They are all case-insensitive, so you can write `RETURNS:` or `params:`.

    __Examples__

    Experimental support. You need code fences and an extra blank line at the end
    so they can be highlighted _and_ recognized by `pytest`.
    Check https://github.com/pawamoy/mkdocstrings/issues/52 for updates.

        ```python
        >>> 2 + 2 == 4
        True

        ```

    """


## Real docstring examples

<!-- This reference only works because we are manually adding PYTHONPATH in GH Actions -->

Check [docs.developers._docstrings_example][] and its source code below.

***

::: docs.developers._docstrings_example
