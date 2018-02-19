%global milestone .0rc1
%{!?upstream_version: %global upstream_version %{version}%{?milestone}}
%global modulename neutron_lbaas
%global servicename neutron-lbaas
%global type LBaaS

# FIXME(ykarel) need to hardcode as neutron_lbaas is not released with neutron
%global neutron_version 12.0.0

%global common_desc \
This is a %{type} service plugin for Openstack Neutron (Networking) service.

%define major_version %(echo %{neutron_version} | awk 'BEGIN { FS=\".\"}; {print $1}')
%define next_version %(echo $((%{major_version} + 1)))

Name:           openstack-%{servicename}
Version:        12.0.0
Release:        0.1%{?milestone}%{?dist}
Epoch:          1
Summary:        Openstack Networking %{type} plugin

License:        ASL 2.0
URL:            http://launchpad.net/neutron/
Source0:        https://tarballs.openstack.org/%{servicename}/%{servicename}-%{upstream_version}.tar.gz
#
# patches_base=12.0.0.0rc1
#

Source2:        %{servicename}v2-agent.service
Source3:        %{servicename}-dist.conf

BuildArch:      noarch
BuildRequires:  gawk
BuildRequires:  openstack-macros
BuildRequires:  python2-devel
BuildRequires:  python2-barbicanclient
BuildRequires:  python-neutron >= %{epoch}:%{major_version}
BuildConflicts: python-neutron >= %{epoch}:%{next_version}
BuildRequires:  python-neutron-lib
BuildRequires:  python2-pbr >= 2.0.0
BuildRequires:  python2-pyasn1
BuildRequires:  python2-pyasn1-modules
BuildRequires:  python2-setuptools
BuildRequires:  systemd
BuildRequires:	git
# Test deps
BuildRequires:  python2-cryptography

Requires:       python-%{servicename} = %{epoch}:%{version}-%{release}
Requires:       openstack-neutron >= %{epoch}:%{major_version}
Conflicts:      openstack-neutron >= %{epoch}:%{next_version}

# This is not a hard dependency, but it's required by the default lbaas driver
Requires:       haproxy

%description
%{common_desc}


%package -n python-%{servicename}
Summary:        Neutron %{type} Python libraries
Group:          Applications/System

Requires:       python-neutron >= %{epoch}:%{major_version}
Conflicts:      python-neutron >= %{epoch}:%{next_version}
Requires:       python2-alembic >= 0.8.10
Requires:       python2-barbicanclient >= 4.0.0
Requires:       python2-cryptography >= 1.7.2
Requires:       python2-eventlet >= 0.18.2
Requires:       python2-keystoneauth1 >= 3.3.0
Requires:       python2-netaddr >= 0.7.18
Requires:       python-neutron-lib >= 1.13.0
Requires:       python2-oslo-config >= 2:5.1.0
Requires:       python2-oslo-db >= 4.27.0
Requires:       python2-oslo-log >= 3.36.0
Requires:       python2-oslo-messaging >= 5.29.0
Requires:       python2-oslo-serialization >= 2.18.0
Requires:       python2-oslo-service >= 1.24.0
Requires:       python2-oslo-reports >= 1.18.0
Requires:       python2-oslo-utils >= 3.33.0
Requires:       python2-pbr >= 2.0.0
Requires:       python2-pyasn1
Requires:       python2-pyasn1-modules
Requires:       python2-requests >= 2.14.2
Requires:       python2-six >= 1.10.0
Requires:       python2-sqlalchemy >= 1.0.10
Requires:       python2-stevedore >= 1.20.0
Requires:       python2-pyOpenSSL >= 16.2.0


%description -n python-%{servicename}
%{common_desc}

This package contains the Neutron %{type} Python library.


%package -n python-%{servicename}-tests
Summary:        Neutron %{type} tests
Group:          Applications/System

Requires:       python-%{servicename} = %{epoch}:%{version}-%{release}
Requires:       python2-fixtures >= 3.0.0
Requires:       python2-mock >= 2.0
Requires:       python2-subunit >= 0.0.18
Requires:       python-requests-mock >= 1.1
Requires:       python2-oslo-concurrency >= 3.25.0
Requires:       python2-oslotest >= 1.10.0
Requires:       python2-testrepository >= 0.0.18
Requires:       python2-testresources >= 0.2.4
Requires:       python2-testtools >= 1.4.0
Requires:       python2-testscenarios >= 0.4
Requires:       python-webob >= 1.7.1
Requires:       python2-tempest >= 14.0.0


%description -n python-%{servicename}-tests
%{common_desc}

This package contains Neutron %{type} test files.


%prep
%autosetup -n %{servicename}-%{upstream_version} -S git

# Let's handle dependencies ourselves
%py_req_cleanup

# Kill egg-info in order to generate new SOURCES.txt
rm -rf %{modulename}.egg-info

%build
export PBR_VERSION=%{version}
export SKIP_PIP_INSTALL=1
%{__python2} setup.py build

# Generate configuration files
PYTHONPATH=. tools/generate_config_file_samples.sh
find etc -name *.sample | while read filename
do
    filedir=$(dirname $filename)
    file=$(basename $filename .sample)
    mv ${filename} ${filedir}/${file}
done

# Loop through values in neutron-lbaas-dist.conf and make sure that the values
# are substituted into the lbaas_agent.ini as comments.
while read name eq value; do
  if [ -n "$name" -a -n "$value" ]; then
    sed -ri "0,/^(#)? *$name *=/{s!\(^(#)? *$name *=\).*!\1 $value!}" etc/lbaas_agent.ini
  fi
done < %{SOURCE3}


%install
export PBR_VERSION=%{version}
export SKIP_PIP_INSTALL=1
%{__python2} setup.py install -O1 --skip-build --root %{buildroot}

# Move rootwrap files to proper location
install -d -m 755 %{buildroot}%{_datarootdir}/neutron/rootwrap
mv %{buildroot}/usr/etc/neutron/rootwrap.d/*.filters %{buildroot}%{_datarootdir}/neutron/rootwrap

# Move config files to proper location
install -d -m 755 %{buildroot}%{_sysconfdir}/neutron

# The generated config files are not moved automatically by setup.py
mv etc/*.ini etc/*.conf %{buildroot}%{_sysconfdir}/neutron

# Install systemd units
install -p -D -m 644 %{SOURCE2} %{buildroot}%{_unitdir}/%{servicename}v2-agent.service

# Install dist conf
install -p -D -m 640 %{SOURCE3} %{buildroot}%{_datadir}/neutron/%{servicename}-dist.conf

# Create configuration directories that can be populated by users with custom *.conf files
mkdir -p %{buildroot}/%{_sysconfdir}/neutron/conf.d/%{servicename}v2-agent

# Make sure neutron-server loads new configuration file
mkdir -p %{buildroot}/%{_datadir}/neutron/server
ln -s %{_sysconfdir}/neutron/%{modulename}.conf %{buildroot}%{_datadir}/neutron/server/%{modulename}.conf

%py2_entrypoint %{modulename} %{servicename}

%post
%systemd_post %{servicename}v2-agent.service


%preun
%systemd_preun %{servicename}v2-agent.service


%postun
%systemd_postun_with_restart %{servicename}v2-agent.service


%files
%license LICENSE
%doc AUTHORS CONTRIBUTING.rst README.rst
%{_bindir}/%{servicename}v2-agent
%{_unitdir}/%{servicename}v2-agent.service
%{_datarootdir}/neutron/rootwrap/lbaas-haproxy.filters
%config(noreplace) %attr(0640, root, neutron) %{_sysconfdir}/neutron/lbaas_agent.ini
%config(noreplace) %attr(0640, root, neutron) %{_sysconfdir}/neutron/%{modulename}.conf
%config(noreplace) %attr(0640, root, neutron) %{_sysconfdir}/neutron/services_lbaas.conf
%dir %{_sysconfdir}/neutron/conf.d
%dir %{_sysconfdir}/neutron/conf.d/%{servicename}v2-agent
%attr(-, root, neutron) %{_datadir}/neutron/%{servicename}-dist.conf
%{_datadir}/neutron/server/%{modulename}.conf


%files -n python-%{servicename}
%{python2_sitelib}/%{modulename}
%{python2_sitelib}/%{modulename}-%{version}-py%{python2_version}.egg-info
%exclude %{python2_sitelib}/%{modulename}/tests


%files -n python-%{servicename}-tests
%{python2_sitelib}/%{modulename}/tests
%{python2_sitelib}/%{modulename}_tests.egg-info

%changelog
* Mon Feb 19 2018 RDO <dev@lists.rdoproject.org> 1:12.0.0-0.1.0rc1
- Update to 12.0.0.0rc1

