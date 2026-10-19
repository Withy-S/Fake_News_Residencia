# Classe principal: prepara uma VM Ubuntu vazia até a stack do Fake News no ar
# (API + Prometheus + Grafana via docker compose).
#
# Os valores dos parâmetros vêm do Hiera (infra/puppet/data/*.yaml).
class fakenews (
  String               $repo_url,
  String               $branch,
  String               $install_dir,
  Hash[String, String] $api_env,
  Sensitive[String]    $grafana_admin_password,
  Array[String]        $firewall_allow,
  String               $healthcheck_url,
  Integer[1]           $healthcheck_max_failures,
) {
  contain fakenews::firewall
  contain fakenews::docker
  contain fakenews::maintenance
  contain fakenews::app
  contain fakenews::service
  contain fakenews::healthcheck

  # docker antes do app; qualquer mudança no app (código ou .env) avisa o serviço.
  Class['fakenews::docker']
  -> Class['fakenews::app']
  ~> Class['fakenews::service']
  -> Class['fakenews::healthcheck']
}
