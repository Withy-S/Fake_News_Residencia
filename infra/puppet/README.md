# infra/puppet — provisionamento com Puppet

Leva uma VM Ubuntu vazia até a stack do projeto no ar (API :8000, Prometheus :9090,
Grafana :3000), com um comando só e sem depender de módulos externos.

## O que o módulo `fakenews` faz

| Classe | Responsabilidade |
|---|---|
| `fakenews::docker` | Instala `docker.io`, `docker-compose-v2` (o `docker compose` com espaço) e `git`; liga o serviço `docker` |
| `fakenews::app` | Clona o repositório em `/opt/fakenews`, mantém igual à branch configurada e gera `backend/.env` e `.env` (senha do Grafana) |
| `fakenews::service` | Cria o serviço systemd `fakenews`, que roda `docker compose up -d --build` e sobe junto com a máquina |
| `fakenews::healthcheck` | Timer que chama o `/api/v1/health` a cada minuto e reinicia a stack depois de 3 falhas seguidas (log: `journalctl -t fakenews-healthcheck`) |
| `fakenews::firewall` | Liga o `ufw` bloqueando tudo que entra, exceto as regras de `fakenews::firewall_allow` (padrão: só SSH) |
| `fakenews::maintenance` | Limita os logs dos containers (3 × 10 MB) e limpa imagens e cache de build sem uso todo domingo às 03:00, sem tocar nos volumes |

A ordem é `docker → app → service → healthcheck`. Se o código ou algum `.env` mudar, o serviço
recebe um *reload* (`docker compose up -d --build`), que só recria os containers alterados.

> A pasta `/opt/fakenews` pertence ao Puppet: alterações feitas à mão nela são
> descartadas na próxima execução.

## Configuração (Hiera)

- `data/common.yaml`: valores padrão (repositório, branch, pasta, variáveis `FN_*` da API).
- `data/secrets.yaml`: segredos, fora do git. Crie a partir do exemplo:

```bash
cp data/secrets.yaml.example data/secrets.yaml
```

## Testando numa VM (Mac)

Testado para Ubuntu 22.04/24.04. Com o [Multipass](https://multipass.run):

```bash
brew install --cask multipass
multipass launch 24.04 --name fakenews --cpus 2 --memory 4G --disk 40G   # folga para as imagens e o cache de build do Docker
multipass transfer --recursive infra/puppet fakenews:/home/ubuntu/
multipass shell fakenews
```

Dentro da VM:

```bash
sudo apt update
sudo apt install -y puppet-agent || sudo apt install -y puppet   # o nome do pacote muda por versão do Ubuntu
cd ~/puppet
cp data/secrets.yaml.example data/secrets.yaml   # e troque a senha
sudo ./apply.sh --noop   # mostra o que vai mudar, sem alterar nada
sudo ./apply.sh          # aplica
```

Rode `sudo ./apply.sh` uma segunda vez: ele não deve mudar nada, porque o Puppet é
idempotente.

Para acessar pelo navegador do Mac, use o IP da VM (`multipass info fakenews`).
O `docker-compose.yml` publica as portas só em `127.0.0.1`, então dentro da VM use
`curl http://127.0.0.1:8000/api/v1/health`, ou abra um túnel:

```bash
ssh -L 3000:127.0.0.1:3000 ubuntu@<ip-da-vm>   # depois abra http://localhost:3000
```
