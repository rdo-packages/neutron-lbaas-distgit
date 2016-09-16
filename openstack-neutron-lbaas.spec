%{!?upstream_version: %global upstream_version %{version}%{?milestone}}
%global modulename neutron_lbaas
%global servicename neutron-lbaas
%global type LBaaS
%global min_neutron_version 1:8.0.0

Name:           openstack-%{servicename}
Version:        XXX
Release:        XXX%{?dist}
Epoch:          1
Summary:        Openstack Networking %{type} plugin

License:        ASL 2.0
URL:            http://launchpad.net/neutron/
Source0:        https://tarballs.openstack.org/%{servicename}/%{servicename}-%{upstream_version}.tar.gz
Source2:        %{servicename}v2-agent.service
Source3:        %{servicename}-dist.conf

BuildArch:      noarch
BuildRequires:  python2-devel
BuildRequires:  python-barbicanclient
BuildRequires:  python-neutron >= %{min_neutron_version}
BuildRequires:  python-neutron-lib
BuildRequires:  python-pbr
BuildRequires:  python-pyasn1
BuildRequires:  python-pyasn1-modules
BuildRequires:  python-setuptools
BuildRequires:  systemd-units
BuildRequires:	git
# Test deps
BuildRequires:  python-cryptography

Requires:       python-%{servicename} = %{epoch}:%{version}-%{release}
Requires:       openstack-neutron >= %{min_neutron_version}
Requires:       python-neutron-lib >= 0.4.0

%description
This is a %{type} service plugin for Openstack Neutron (Networking) service.


%package -n python-%{servicename}
Summary:        Neutron %{type} Python libraries
Group:          Applications/System

Requires:       python-neutron >= %{min_neutron_version}
Requires:       python-alembic >= 0.8.4
Requires:       python-barbicanclient >= 4.0.0
Requires:       python-eventlet
Requires:       python-keystoneauth1 >= 2.10.0
Requires:       python-netaddr >= 0.7.12
Requires:       python-oslo-config >= 2:3.14.0
Requires:       python-oslo-db >= 4.10.0
Requires:       python-oslo-log >= 1.14.0
Requires:       python-oslo-messaging >= 5.2.0
Requires:       python-oslo-serialization >= 1.10.0
Requires:       python-oslo-service >= 1.10.0
Requires:       python-oslo-reports >= 0.6.0
Requires:       python-oslo-utils >= 3.16.0
Requires:       python-pbr
Requires:       python-pyasn1
Requires:       python-pyasn1-modules
Requires:       python-requests
Requires:       python-six >= 1.9.0
Requires:       python-sqlalchemy >= 1.0.10
Requires:       python-stevedore >= 1.16.0
Requires:       pyOpenSSL


%description -n python-%{servicename}
This is a %{type} service plugin for Openstack Neutron (Networking) service.

This package contains the Neutron %{type} Python library.


%package -n python-%{servicename}-tests
Summary:        Neutron %{type} tests
Group:          Applications/System

Requires:       python-%{servicename} = %{epoch}:%{version}-%{release}


%description -n python-%{servicename}-tests
This is a %{type} service plugin for Openstack Neutron (Networking) service.

This package contains Neutron %{type} test files.


%prep
%autosetup -n %{servicename}-%{upstream_version} -S git

# Let's handle dependencies ourselves
rm -f requirements.txt

# Kill egg-info in order to generate new SOURCES.txt
rm -rf neutron_lbaas.egg-info

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
%config(noreplace) %attr(0640, root, neutron) %{_sysconfdir}/neutron/neutron_lbaas.conf
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


%changelog
