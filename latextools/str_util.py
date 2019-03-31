def prefix_lines(prefix, text, clean=True):
    prefixed_lines = (prefix + line
                      for line in text.split('\n'))
    if clean:
        prefixed_lines = map(str.rstrip, prefixed_lines)
    return '\n'.join(prefixed_lines)
