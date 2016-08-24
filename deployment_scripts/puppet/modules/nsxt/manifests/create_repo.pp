class nsxt::create_repo (
  $repo_dir       = '/opt/nsx-t-repo',
  $repo_file      = '/etc/apt/sources.list.d/nsx-t-local.list',
  $repo_pref_file = '/etc/apt/preferences.d/nsx-t-local.pref',
) {
  file { $repo_dir:
    ensure  => directory,
    mode    => '0755',
    source  => "puppet:///modules/${module_name}/packages",
    recurse => true,
    force   => true,
  }
  file { $repo_file:
    ensure  => file,
    mode    => '0644',
    content => "deb file:${repo_dir} /",
    replace => true,
  }
  file { $repo_pref_file:
    ensure  => file,
    mode    => '0644',
    source  => "puppet:///modules/${module_name}/pinning",
    replace => true,
  }
  exec { 'Create repo':
    path     => '/usr/sbin:/usr/bin:/sbin:/bin',
    command  => "cd ${repo_dir} && dpkg-scanpackages . /dev/null | gzip -9c > Packages.gz",
    provider => 'shell',
    require  => File[$repo_dir],
  }
}
