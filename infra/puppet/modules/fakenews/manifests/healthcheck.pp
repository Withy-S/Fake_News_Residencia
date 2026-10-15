# Auto-cura: um timer do systemd chama o /health da API a cada minuto e
# reinicia a stack depois de algumas falhas seguidas.
class fakenews::healthcheck {
  file { '/usr/local/bin/fakenews-healthcheck':
    ensure  => file,
    mode    => '0755',
    content => epp('fakenews/healthcheck.sh.epp', {
      'url'          => $fakenews::healthcheck_url,
      'max_failures' => $fakenews::healthcheck_max_failures,
    }),
  }

  file { '/etc/systemd/system/fakenews-healthcheck.service':
    ensure => file,
    source => 'puppet:///modules/fakenews/fakenews-healthcheck.service',
    notify => Exec['fakenews-healthcheck-daemon-reload'],
  }

  file { '/etc/systemd/system/fakenews-healthcheck.timer':
    ensure => file,
    source => 'puppet:///modules/fakenews/fakenews-healthcheck.timer',
    notify => Exec['fakenews-healthcheck-daemon-reload'],
  }

  exec { 'fakenews-healthcheck-daemon-reload':
    command     => 'systemctl daemon-reload',
    path        => ['/usr/bin', '/bin'],
    refreshonly => true,
  }

  service { 'fakenews-healthcheck.timer':
    ensure  => running,
    enable  => true,
    require => [
      File['/usr/local/bin/fakenews-healthcheck'],
      Exec['fakenews-healthcheck-daemon-reload'],
    ],
  }
}
