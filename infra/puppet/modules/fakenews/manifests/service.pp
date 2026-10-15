# Serviço systemd que sobe a stack no boot. Quando o código ou o .env mudam,
# o Puppet faz "reload" (docker compose up -d --build), que só recria os
# containers alterados, sem derrubar o resto.
class fakenews::service {
  file { '/etc/systemd/system/fakenews.service':
    ensure  => file,
    content => epp('fakenews/fakenews.service.epp', { 'dir' => $fakenews::install_dir }),
    notify  => Exec['fakenews-daemon-reload'],
  }

  exec { 'fakenews-daemon-reload':
    command     => 'systemctl daemon-reload',
    path        => ['/usr/bin', '/bin'],
    refreshonly => true,
  }

  service { 'fakenews':
    ensure     => running,
    enable     => true,
    hasrestart => true,
    restart    => 'systemctl reload fakenews',
    require    => Exec['fakenews-daemon-reload'],
  }
}
