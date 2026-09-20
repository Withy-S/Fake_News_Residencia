from app.services.whitelist import extract_host, is_trusted_domain

TRUSTED = ["gov.br", "who.int"]


def test_extract_host_normaliza_para_minusculas():
    assert extract_host("https://WWW.Gov.BR/noticia") == "www.gov.br"


def test_extract_host_sem_url():
    assert extract_host(None) is None
    assert extract_host("") is None


def test_dominio_exato_e_confiavel():
    assert is_trusted_domain("https://gov.br/x", TRUSTED)


def test_subdominio_e_confiavel():
    assert is_trusted_domain("https://saude.gov.br/x", TRUSTED)


def test_dominio_parecido_nao_e_confiavel():
    assert not is_trusted_domain("https://evilgov.br/x", TRUSTED)


def test_dominio_confiavel_dentro_de_outro_nao_passa():
    assert not is_trusted_domain("https://gov.br.evil.com/x", TRUSTED)


def test_truque_com_arroba_nao_passa():
    assert not is_trusted_domain("https://gov.br@evil.com/x", TRUSTED)


def test_sem_url_nao_e_confiavel():
    assert not is_trusted_domain(None, TRUSTED)


def test_lista_vazia_nao_confia_em_ninguem():
    assert not is_trusted_domain("https://gov.br/x", [])
