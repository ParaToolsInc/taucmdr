#!/bin/bash
here="`cd ${0%/*} && pwd -P`"

function abort {
  echo "Fatal error.  See stdout"
  exit 1
}

PROJECT_ROOT="$here/.."
PACKAGE_ROOT="$here"

VERSION=`cat $PROJECT_ROOT/VERSION`

PROJECT_FILES=(LICENSE README.md bin examples packages build.sh setup.py)
PACKAGE_FILES=(debian debian_build.sh)

builddir=taucmdr-$VERSION
tarfile=taucmdr_${VERSION}-1.tar.gz

mkdir $builddir || abort

cat > debian_build.sh <<EOF
#!/bin/bash

prefix=/opt/paratools/taucmdr-$VERSION
EOF
cat >> debian_build.sh <<"EOF"
buildroot=/usr/src/packages/BUILD/debian/taucmdr

dirname="`ls build`"
mkdir -p $buildroot/$prefix/bin
mkdir -p $buildroot/usr/local/bin
mv build/$dirname examples LICENSE $buildroot/$prefix
pushd $buildroot/$prefix/bin
ln -s ../$dirname/taucmdr .
popd
ln -s $prefix/bin/taucmdr $buildroot/usr/local/bin/taucmdr
find $buildroot
EOF

for file in ${PROJECT_FILES[@]} ; do
  cp -a $PROJECT_ROOT/$file $builddir || abort
done

for file in ${PACKAGE_FILES[@]} ; do
  cp -a $PACKAGE_ROOT/$file $builddir || abort
done

find $builddir -name '*.pyc' -delete
find $builddir -name '.DS_Store' -delete
find $builddir -name '._*' -delete
tar czf $tarfile $builddir || abort
rm -rf $builddir || abort

tarsize=`/usr/bin/stat -c%s $tarfile`
tarsha1=`shasum $tarfile | cut -d' ' -f1`
tarsha256=`shasum -a 256 $tarfile | cut -d' ' -f1`
tarmd5=`openssl dgst -md5 $tarfile | cut -d= -f2`

cat > taucmdr.dsc <<EOF
Format: 1.0
Source: taucmdr
Binary: taucmdr
Architecture: any
Version: ${VERSION}-1
Maintainer: John C. Linford <jlinford@paratools.com>
Homepage: http://www.paratools.com/taucmdr
Standards-Version: 3.8.1
Build-Depends: cdbs (>= 0.4.49), debhelper (>= 4.1.16), python, python-support, cx-freeze (>= 4.3)
Checksums-Sha1: 
 $tarsha1 $tarsize $tarfile
Checksums-Sha256: 
 $tarsha256 $tarsize $tarfile
Files: 
 $tarmd5 $tarsize $tarfile
EOF

cat > taucmdr.spec <<EOF
# norootforbuild

%define packagesdir /opt/paratools
%define _prefix %{packagesdir}/%{name}-%{version}

# Don't fiddle with my binary files!
%global _enable_debug_package 0
%global debug_package %{nil}
%global __os_install_post /usr/lib/rpm/brp-compress %{nil}

Name:           taucmdr
Version:        $VERSION
Release:        1
License:        BSD
Summary:        Software performance engineering made easy
Url:            http://www.paratools.com/taucmdr
Group:          Development/Tools
Source:         $tarfile
BuildRequires:  python python-devel cx-freeze
BuildRequires: -post-build-checks
Provides:       %{name} = %{version}-%{release}
Provides:       %{name} = %{version}
AutoReq:        yes
AutoProv:       no
BuildRoot:      %{_tmppath}/%{name}-%{version}-build
Prefix:         %{packagesdir}
EOF
cat >> taucmdr.spec <<"EOF"

%description
TAU Commander presents a simple, intuitive, and systemized interface that guides users through performance engineering workflows and offers constructive feedback in case of error. TAU Commander also enhances the performance engineer's ability to mine actionable information from the application performance data by connecting to a suite of cloud-based data analysis, storage, visualization, and reporting services.

%prep
%setup -q
%{?_prefix:%__rm -rf "%{_prefix}"}

%build
export PYTHONPATH=$PWD/packages/tau:$PWD/packages:$PYTHONPATH
python setup.py build_exe


%install
export QA_RPATHS=$[ 0x0001|0x0002|0x0008 ]
dirname="`ls build`"

mkdir -p %{buildroot}%{_prefix}/bin
mv build/$dirname examples LICENSE %{buildroot}%{_prefix}
pushd %{buildroot}%{_prefix}/bin
ln -s ../$dirname/tau .
popd
mkdir -p %{buildroot}/usr/local/bin
ln -s %{_prefix}/bin/tau %{buildroot}/usr/local/bin/tau


%clean
%{?buildroot:%__rm -rf "%{buildroot}"}


%post


%postun


%files
%defattr(-,root,root)
%dir %{packagesdir}
%{_prefix}
/usr/local/bin/tau

%changelog
EOF

rm debian_build.sh
echo "All done!  Copy $tarfile, taucmdr.spec, and taucmdr.dsc to the OSC package"
echo cp $tarfile taucmdr.spec taucmdr.dsc "$HOME/osc/home:jlinford/taucmdr"
