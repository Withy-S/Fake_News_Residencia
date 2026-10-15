# Coloca o código na máquina e gera os arquivos de ambiente que não vão para o git.
class fakenews::app {
  $dir    = $fakenews::install_dir
  $branch = $fakenews::branch
  $path   = ['/usr/bin', '/bin', '/usr/sbin', '/sbin']

  exec { 'fakenews-clone':
    command => "git clone --branch ${branch} ${fakenews::repo_url} ${dir}",
    creates => "${dir}/.git",
    path    => $path,
  }

  # Mantém a pasta igual à branch do repositório. A pasta é do Puppet:
  # alterações feitas à mão nela são descartadas.
  exec { 'fakenews-update':
    command  => "git -C ${dir} reset --hard origin/${branch}",
    unless   => "git -C ${dir} fetch -q origin ${branch} && test \"$(git -C ${dir} rev-parse HEAD)\" = \"$(git -C ${dir} rev-parse origin/${branch})\"",
    provider => shell,
    path     => $path,
    require  => Exec['fakenews-clone'],
  }

  # Variáveis da API (FN_*), lidas pelo docker-compose.yml via env_file.
  file { "${dir}/backend/.env":
    ensure  => file,
    mode    => '0600',
    content => epp('fakenews/backend.env.epp', { 'vars' => $fakenews::api_env }),
    require => Exec['fakenews-clone'],
  }

  # .env da raiz: o docker compose lê sozinho e usa no serviço do Grafana.
  file { "${dir}/.env":
    ensure  => file,
    mode    => '0600',
    content => epp('fakenews/compose.env.epp', {
      'grafana_admin_password' => $fakenews::grafana_admin_password,
    }),
    require => Exec['fakenews-clone'],
  }
}
