# Evita que o disco encha: limita os logs dos containers e limpa imagens e
# cache de build sem uso toda semana. Volumes (dados do Grafana e do
# Prometheus) não são tocados.
class fakenews::maintenance {
  # Vale para containers criados depois da mudança.
  file { '/etc/docker/daemon.json':
    ensure  => file,
    source  => 'puppet:///modules/fakenews/docker-daemon.json',
    require => Package['docker.io'],
    notify  => Service['docker'],
  }

  file { '/etc/systemd/system/fakenews-prune.service':
    ensure => file,
    source => 'puppet:///modules/fakenews/fakenews-prune.service',
    notify => Exec['fakenews-prune-daemon-reload'],
  }

  file { '/etc/systemd/system/fakenews-prune.timer':
    ensure => file,
    source => 'puppet:///modules/fakenews/fakenews-prune.timer',
    notify => Exec['fakenews-prune-daemon-reload'],
  }

  exec { 'fakenews-prune-daemon-reload':
    command     => 'systemctl daemon-reload',
    path        => ['/usr/bin', '/bin'],
    refreshonly => true,
  }

  service { 'fakenews-prune.timer':
    ensure  => running,
    enable  => true,
    require => Exec['fakenews-prune-daemon-reload'],
  }
}
