# Public sample issue

The public scorer is a placeholder.

Bug summary:

`normalize_label(value)` should safely handle `None` input by returning an empty string. Current behavior crashes when value is `None`.

Serious CODE-01 evaluation should replace this with a real repo fixture and hidden tests.
