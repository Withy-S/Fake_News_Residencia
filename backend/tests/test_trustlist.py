from app.services.trustlist import extract_host, is_trusted_domain

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


def test_www_na_url_e_na_configuracao():
    assert is_trusted_domain("https://www.who.int/noticia", ["who.int"])
    assert is_trusted_domain("https://who.int/noticia", ["www.who.int"])


def test_normaliza_configuracao_e_ponto_final():
    assert is_trusted_domain("https://WWW.WHO.INT./noticia", [" WWW.WHO.INT. "])


def test_dominio_desconhecido():
    assert not is_trusted_domain("https://example.org/noticia", TRUSTED)


def test_url_malformada():
    assert not is_trusted_domain("https://[invalido", TRUSTED)


def test_carrega_whitelist_do_ambiente(monkeypatch):
    from app.core.config import Settings

    monkeypatch.setenv("FN_TRUSTED_DOMAINS", '["who.int", "gov.br"]')
    settings = Settings(_env_file=None)
    assert settings.trusted_domains == ["who.int", "gov.br"]
    assert is_trusted_domain("https://www.who.int/x", settings.trusted_domains)


def test_carrega_whitelist_do_arquivo_env(tmp_path, monkeypatch):
    from app.core.config import Settings

    monkeypatch.delenv("FN_TRUSTED_DOMAINS", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text('FN_TRUSTED_DOMAINS=["who.int"]\n')
    assert Settings(_env_file=env_file).trusted_domains == ["who.int"]
