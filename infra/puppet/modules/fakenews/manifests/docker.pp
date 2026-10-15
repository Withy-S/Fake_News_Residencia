# Instala o Docker e o plugin do Compose (garante o "docker compose" com espaço)
# usando os pacotes do próprio Ubuntu, sem depender de módulos externos.
class fakenews::docker {
  package { ['docker.io', 'docker-compose-v2', 'git']:
    ensure => installed,
  }

  service { 'docker':
    ensure  => running,
    enable  => true,
    require => Package['docker.io'],
  }
}
