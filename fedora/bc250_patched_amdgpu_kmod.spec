### spec file based on linux-cachyos (https://github.com/CachyOS/linux-cachyos/tree/master/linux-cachyos) for the Fedora operating system.
### Licensed as GPLv3
### The authors of linux-cachyos patchset (Not used here):
# Peter Jung ptr1337 <admin@ptr1337.dev>
# Piotr Gorski sirlucjan <piotrgorski@cachyos.org>
### The port maintainer for Fedora:
# bieszczaders <zbyszek@linux.pl>
# https://copr.fedorainfracloud.org/coprs/bieszczaders/
%global _default_patch_fuzz 2

%define _build_id_links none
%define _disable_source_fetch 1

# See https://fedoraproject.org/wiki/Changes/SetBuildFlagsBuildCheck to why this has to be done
%if 0%{?fedora} >= 37
%undefine _auto_set_build_flags
%endif

%ifarch x86_64
%define karch x86
%define asmarch x86
%endif

# define git branch to make testing easier without merging to master branch
%define _git_branch master

# whether to build kernel with llvm compiler(clang)
%define llvm_kbuild 0
%if %{llvm_kbuild}
%define llvm_build_env_vars CC=clang CXX=clang++ LD=ld.lld LLVM=1 LLVM_IAS=1
%define ltoflavor 1
%endif

Name: bc250-patched-amdgpu-kmod
Summary: The patched kernel modules amdgpu with parameter to enable 40 compute units on AMD BC250 GPU

%define _basekver @@BASEKVER@@
%define _stablekver @@STABLEKVER@@
%if %{_stablekver} == 0
%define _tarkver %{_basekver}
%else
%define _tarkver %{_basekver}.%{_stablekver}
%endif

Version: %{_basekver}.%{_stablekver}

%define ogcver @@OGCVER@@
%define buildnum @@BUILDNUM@@
Release: ogc%{ogcver}.%{buildnum}%{?dist}

# Define rawhide fedora version
%define _rawhidever 44

%define rpmver %{version}-%{release}
%define krelstr %{release}.%{_arch}
%define kverstr %{version}-%{krelstr}

License: GPLv2 and Redistributable, no modifications permitted
Group: System Environment/Kernel
Vendor: The Linux Community and OGC maintainer(s)
URL: https://opengamingcollective.org
Source0: linux-%{_tarkver}.tar.xz
Source1: config
# needed for kernel-tools
Source2: kvm_stat.logrotate

# https://fedoraproject.org/wiki/Changes/EncourageI686LeafRemoval
ExcludeArch:    %{ix86}

# Stable patches
Patch0: monolithic.patch
Patch1: bc250-40cu-amdgpu.patch

%define __spec_install_post /usr/lib/rpm/brp-compress || :
%define debug_package %{nil}
# Default compression algorithm
%global compression xz
%global compression_flags --compress
%global compext xz

BuildRequires: make
BuildRequires: gcc
BuildRequires: bc
BuildRequires: bison
BuildRequires: flex
BuildRequires: binutils
BuildRequires: binutils-devel
BuildRequires: elfutils-libelf-devel
BuildRequires: openssl-devel
BuildRequires: kmod
BuildRequires: patch
%if %{llvm_kbuild}
BuildRequires: clang
BuildRequires: llvm
BuildRequires: lld
%endif
BuildRequires: kernel-devel-%{rpmver} = %{kverstr}
BuildRequires: kernel-core-%{rpmver} = %{kverstr}


%description
This package contains the patched amdgpu kernel module with parameter to enable 40 compute units on AMD BC250 GPU. It is built against the same kernel version as the mainline kernel, so it can be used as a drop-in replacement for the amdgpu module provided by the mainline kernel.

%prep
%setup -q -n linux-%{_tarkver}

# Apply OGC patch
patch -p1 -i %{PATCH0}

# Apply BC250 patch
patch -p1 -i %{PATCH1}

# Copy the full kernel configuration to the build directory to ensure all necessary options are available during module compilation
cp /lib/modules/%{kverstr}/config .config

# Copy Modules.symvers to be used during module build
cp /usr/src/kernels/%{kverstr}/Module.symvers .

# Save configuration for later reuse
cat .config > config-linux-ogc

%build

make %{?_smp_mflags} %{?llvm_build_env_vars} EXTRAVERSION=-%{krelstr} prepare modules_prepare
make %{?_smp_mflags} %{?llvm_build_env_vars} EXTRAVERSION=-%{krelstr} M=drivers/gpu/drm/amd/amdgpu modules


%install
mkdir -p %{buildroot}/lib/modules/%{kverstr}/updates/drivers/gpu/drm/amd/amdgpu

install -m 0755 drivers/gpu/drm/amd/amdgpu/amdgpu.ko \
    %{buildroot}/lib/modules/%{kverstr}/updates/drivers/gpu/drm/amd/amdgpu/amdgpu.ko

%clean
rm -rf %{buildroot}

%post 
/sbin/depmod -a %{kverstr}
dracut -f --kver %{kverstr}



%files 
/lib/modules/%{kverstr}/updates/drivers/gpu/drm/amd/amdgpu/amdgpu.ko

%changelog
* Thu May 21 2026 Filippo Rossoni <filippo.rossoni@gmail.com> - 6.19.14-ogc5-1
- Initial build of patched amdgpu module
