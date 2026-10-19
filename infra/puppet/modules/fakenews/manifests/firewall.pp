# Firewall (ufw): bloqueia tudo que entra, exceto as regras de $firewall_allow.
# As portas da stack já ficam presas em 127.0.0.1 pelo docker-compose.yml.
class fakenews::firewall {
  $path = ['/usr/sbin', '/usr/bin', '/sbin', '/bin']

  package { 'ufw':
    ensure => installed,
  }

  exec { 'ufw-default-deny-incoming':
    command => 'ufw default deny incoming',
    unless  => 'grep -q \'^DEFAULT_INPUT_POLICY="DROP"\' /etc/default/ufw',
    path    => $path,
    require => Package['ufw'],
  }

  $fakenews::firewall_allow.each |String $rule| {
    exec { "ufw-allow-${rule}":
      command  => "ufw allow ${rule}",
      unless   => "ufw show added | grep -qxF 'ufw allow ${rule}'",
      provider => shell,
      path     => $path,
      require  => Package['ufw'],
      before   => Exec['ufw-enable'],
    }
  }

  # Só liga depois das regras: ligar sem liberar o SSH tranca a máquina.
  exec { 'ufw-enable':
    command => 'ufw --force enable',
    unless  => 'ufw status | grep -q "Status: active"',
    path    => $path,
    require => Exec['ufw-default-deny-incoming'],
  }
}
