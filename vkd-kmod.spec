%global	kmod_name vkd

#global	debug_package %{nil}

# Generate kernel symbols requirements:
%global _use_internal_dependency_generator 0

# If kversion isn't defined on the rpmbuild line, define it here. For Fedora,
# kversion needs always to be defined as there is no kABI support.

# RHEL 7.9:
%if 0%{?rhel} == 7
%{!?kversion: %global kversion 3.10.0-1160.11.1.el7}
%endif

Name:           %{kmod_name}-kmod
Version:        6.3.0
Release:        1%{?dist}
Summary:        Luna PCI driver
License:        Safenet
URL:            https://cpl.thalesgroup.com/encryption/hardware-security-modules/general-purpose-hsms

Source0:        %{kmod_name}-%{version}.tar.gz

BuildRequires:  elfutils-libelf-devel
BuildRequires:  gcc
BuildRequires:  kernel-devel %{?kversion:== %{kversion}}
BuildRequires:  kernel-abi-whitelists %{?kversion:== %{kversion}}
BuildRequires:  kmod
BuildRequires:  redhat-rpm-config

%description
Luna PCI-1200 and PCI-7000 Driver (PCI Crypto Controller).

%package -n kmod-%{kmod_name}
Summary:    %{kmod_name} kernel module(s)

Provides:   kabi-modules = %{kversion}.%{_target_cpu}
Provides:   %{kmod_name}-kmod = %{?epoch:%{epoch}:}%{version}-%{release}
Requires:   module-init-tools

%description -n kmod-%{kmod_name}
Luna PCI-1200 and PCI-7000 Driver (PCI Crypto Controller).

This package provides the %{kmod_name} kernel module(s) built for the Linux kernel
using the %{_target_cpu} family of processors.

%post -n kmod-%{kmod_name}
if [ -e "/boot/System.map-%{kversion}.%{_target_cpu}" ]; then
    /usr/sbin/depmod -aeF "/boot/System.map-%{kversion}.%{_target_cpu}" "%{kversion}.%{_target_cpu}" > /dev/null || :
fi
modules=( $(find /lib/modules/%{kversion}.%{_target_cpu}/extra/%{kmod_name} | grep '\.ko$') )
if [ -x "/usr/sbin/weak-modules" ]; then
    printf '%s\n' "${modules[@]}" | /usr/sbin/weak-modules --add-modules
fi

%preun -n kmod-%{kmod_name}
rpm -ql kmod-%{kmod_name}-%{version}-%{release}.%{_target_cpu} | grep '\.ko$' > /var/run/rpm-kmod-%{kmod_name}-modules

%postun -n kmod-%{kmod_name}
if [ -e "/boot/System.map-%{kversion}.%{_target_cpu}" ]; then
    /usr/sbin/depmod -aeF "/boot/System.map-%{kversion}.%{_target_cpu}" "%{kversion}.%{_target_cpu}" > /dev/null || :
fi
modules=( $(cat /var/run/rpm-kmod-%{kmod_name}-modules) )
rm /var/run/rpm-kmod-%{kmod_name}-modules
if [ -x "/usr/sbin/weak-modules" ]; then
    printf '%s\n' "${modules[@]}" | /usr/sbin/weak-modules --remove-modules
fi

%prep
%autosetup -p1 -n %{kmod_name}-%{version}

mv driver/vkd-linux-2.6.mf driver/Makefile
mv utils/utils-linux-2.4.mf utils/Makefile
sed -i -e 's/EXTRA_CFLAGS =/EXTRA_CFLAGS = $(CFLAGS)/g' \
    utils/Makefile driver/Makefile

echo "override %{kmod_name} * weak-updates/%{kmod_name}" > kmod-%{kmod_name}.conf

%build
%set_build_flags
make -C %{_usrsrc}/kernels/%{kversion}.%{_target_cpu} M=$PWD/driver modules
make -C utils

%install
export INSTALL_MOD_PATH=%{buildroot}
export INSTALL_MOD_DIR=extra/%{kmod_name}
make -C %{_usrsrc}/kernels/%{kversion}.%{_target_cpu} M=$PWD/driver modules_install

install -d %{buildroot}%{_sysconfdir}/depmod.d/
install kmod-%{kmod_name}.conf %{buildroot}%{_sysconfdir}/depmod.d/

mkdir -p %{buildroot}%{_bindir}
install -p -m 755 utils/{dumpit,vconfig,vreset} %{buildroot}%{_bindir}

# Remove the unrequired files.
rm -f %{buildroot}/lib/modules/%{kversion}.%{_target_cpu}/modules.*

%files -n kmod-%{kmod_name}
%license COPYING SFNT_Legal.pdf
/lib/modules/%{kversion}.%{_target_cpu}/extra/*
%config /etc/depmod.d/kmod-%{kmod_name}.conf
%{_bindir}/dumpit
%{_bindir}/vconfig
%{_bindir}/vreset

%changelog
* Fri Jan 22 2021 Simone Caronni <negativo17@gmail.com> - 6.3.0-1
- First build based on what is contained in 10.3.0-275 sources.
