def format(text, indent=2, width=70):
    """
    Format a text block.
    
    This function formats a block of text. The text is broken into
    tokens. (Whitespace is NOT preserved.) The tokens are reassembled
    at the specified level of indentation and line width.  A string is
    returned.

    Arguments:
        `text`   -- the string to be reformatted.
        `indent` -- the integer number of spaces to indent by.
        `width`  -- the maximum width of formatted text (including indent).
    """
    width = width - indent
    out = []
    stack = [word for word in text.replace("\n", " ").split(" ") if word]
    while stack:
        line = ""
        while stack:
            if len(line) + len(" " + stack[0]) > width: break
            if line: line += " "
            line += stack.pop(0)
        out.append(" "*indent + line)
    return "\n".join(out)
