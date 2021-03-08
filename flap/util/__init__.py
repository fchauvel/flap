

def truncate(text, length, marker="..."):
    if len(text) <= length:
        return text
    return text[:length - len(marker)] + marker
