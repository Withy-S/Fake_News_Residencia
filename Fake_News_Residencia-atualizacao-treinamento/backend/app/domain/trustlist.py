from urllib.parse import urlparse


def extract_host(url: str | None) -> str | None:
    """Extrai o host de uma URL, em minúsculas e sem ponto final."""
    if not url:
        return None
    try:
        host = urlparse(url).hostname
    except ValueError:
        return None
    return host.rstrip(".") if host else None


def is_trusted_domain(url: str | None, trusted_domains: list[str]) -> bool:
    """True se o host da URL for um domínio da whitelist ou subdomínio dele."""
    host = extract_host(url)
    if host is None:
        return False
    for domain in trusted_domains:
        d = domain.lower().strip().strip(".").removeprefix("www.")
        if d and (host == d or host.endswith("." + d)):
            return True
    return False
