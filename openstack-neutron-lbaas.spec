# Macros for py2/py3 compatibility
%if 0%{?fedora} || 0%{?rhel} > 7
%global pyver %{python3_pkgversion}
%else
%global pyver 2
%endif
%global pyver_bin python%{pyver}
%global pyver_sitelib %python%{pyver}_sitelib
%global pyver_install %py%{pyver}_install
%global pyver_build %py%{pyver}_build
# End of macros for py2/py3 compatibility
%{!?upstream_version: %global upstream_version %{version}%{?milestone}}
%global modulename neutron_lbaas
%global servicename neutron-lbaas
%global type LBaaS

%global common_desc \
This is a %{type} service plugin for Openstack Neutron (Networking) service.

%define major_version %(echo %{version} | awk 'BEGIN { FS=\".\"}; {print $1}')
%define next_version %(echo $((%{major_version} + 1)))

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
BuildRequires:  gawk
BuildRequires:  openstack-macros
BuildRequires:  python%{pyver}-devel
BuildRequires:  python%{pyver}-barbicanclient
BuildRequires:  python%{pyver}-neutron >= %{epoch}:%{major_version}
BuildConflicts: python2-neutron >= %{epoch}:%{next_version}
BuildRequires:  python%{pyver}-neutron-lib
BuildRequires:  python%{pyver}-pbr >= 2.0.0
BuildRequires:  python%{pyver}-pyasn1
BuildRequires:  python%{pyver}-pyasn1-modules
BuildRequires:  python%{pyver}-setuptools
BuildRequires:  systemd
BuildRequires:	git
# Test deps
BuildRequires:  python%{pyver}-cryptography

Requires:       python%{pyver}-%{servicename} = %{epoch}:%{version}-%{release}
Requires:       openstack-neutron >= %{epoch}:%{major_version}
Conflicts:      openstack-neutron >= %{epoch}:%{next_version}

# This is not a hard dependency, but it's required by the default lbaas driver
Requires:       haproxy

%description
%{common_desc}


%package -n python%{pyver}-%{servicename}
Summary:        Neutron %{type} Python libraries
%{?python_provide:%python_provide python%{pyver}-%{servicename}}
Group:          Applications/System

Requires:       python%{pyver}-neutron >= %{epoch}:%{major_version}
Conflicts:      python2-neutron >= %{epoch}:%{next_version}
Requires:       python%{pyver}-alembic >= 0.8.10
Requires:       python%{pyver}-barbicanclient >= 4.5.2
Requires:       python%{pyver}-cryptography >= 2.1
Requires:       python%{pyver}-eventlet >= 0.18.2
Requires:       python%{pyver}-keystoneauth1 >= 3.4.0
Requires:       python%{pyver}-netaddr >= 0.7.18
Requires:       python%{pyver}-neutron-lib >= 1.18.0
Requires:       python%{pyver}-oslo-config >= 2:5.2.0
Requires:       python%{pyver}-oslo-db >= 4.27.0
Requires:       python%{pyver}-oslo-i18n >= 3.15.3
Requires:       python%{pyver}-oslo-log >= 3.36.0
Requires:       python%{pyver}-oslo-messaging >= 5.29.0
Requires:       python%{pyver}-oslo-serialization >= 2.18.0
Requires:       python%{pyver}-oslo-service >= 1.24.0
Requires:       python%{pyver}-oslo-reports >= 1.18.0
Requires:       python%{pyver}-oslo-utils >= 3.33.0
Requires:       python%{pyver}-pbr >= 2.0.0
Requires:       python%{pyver}-pyasn1
Requires:       python%{pyver}-pyasn1-modules
Requires:       python%{pyver}-requests >= 2.14.2
Requires:       python%{pyver}-six >= 1.10.0
Requires:       python%{pyver}-sqlalchemy >= 1.0.10
Requires:       python%{pyver}-stevedore >= 1.20.0
Requires:       python%{pyver}-pyOpenSSL >= 17.1.0


%description -n python%{pyver}-%{servicename}
%{common_desc}

This package contains the Neutron %{type} Python library.


%package -n python%{pyver}-%{servicename}-tests
Summary:        Neutron %{type} tests
%{?python_provide:%python_provide python%{pyver}-%{servicename}-tests}
Group:          Applications/System

Requires:       python%{pyver}-%{servicename} = %{epoch}:%{version}-%{release}
Requires:       python%{pyver}-fixtures >= 3.0.0
Requires:       python%{pyver}-mock >= 2.0
Requires:       python%{pyver}-subunit >= 0.0.18
Requires:       python%{pyver}-oslo-concurrency >= 3.25.0
Requires:       python%{pyver}-oslotest >= 1.10.0
Requires:       python%{pyver}-testrepository >= 0.0.18
Requires:       python%{pyver}-testresources >= 0.2.4
Requires:       python%{pyver}-testtools >= 1.4.0
Requires:       python%{pyver}-testscenarios >= 0.4
Requires:       python%{pyver}-webob >= 1.7.1
Requires:       python%{pyver}-tempest >= 14.0.0

# Handle python2 exception
%if %{pyver} == 2
Requires:       python-requests-mock >= 1.1
%else
Requires:       python%{pyver}-requests-mock >= 1.1
%endif


%description -n python%{pyver}-%{servicename}-tests
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
%{pyver_build}

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
%{pyver_install}

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


%files -n python%{pyver}-%{servicename}
%{pyver_sitelib}/%{modulename}
%{pyver_sitelib}/%{modulename}-%{version}-py%{python2_version}.egg-info
%exclude %{pyver_sitelib}/%{modulename}/tests


%files -n python%{pyver}-%{servicename}-tests
%{pyver_sitelib}/%{modulename}/tests
%{pyver_sitelib}/%{modulename}_tests.egg-info

%changelog
