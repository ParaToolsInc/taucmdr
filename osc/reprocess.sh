#!/bin/bash
here="`cd ${0%/*} && pwd -P`"

PROJECT_ROOT="$here/.."
PACKAGE_ROOT="$here"

PROJECT="home:jlinford"
PACKAGE="taucmdr"
VERSION=`cat $PROJECT_ROOT/VERSION`

function abort()
{
  if [ -n "$1" ] ; then
    echo "ERROR: $1"
  else
    echo "ERROR: Unknown error"
  fi
  exit 1
}

function rpm2tar()
{
  rpmfile="$1"
  stem="`echo $rpmfile | sed -e 's/\.rpm//' -e 's/\.i[356]86//' -e 's/\.x86_64//' -e 's/\.amd64//'`"

  case `echo $rpmfile` in
  *i386*)
    arch=i386
    ;;
  *i586*)
    arch=i586
    ;;
  *i686*)
    arch=i686
    ;;
  *amd64*|*x86_64*)
    arch=x86_64
    ;;
  esac

  end=`echo ${distro}.${arch} | sed -e "s/CentOS_CentOS/CentOS/" -e "s/RedHat_RHEL/RHEL/" -e "s/-mdv2011.0//"`

  rpm2cpio "$rpmfile" | cpio -idm
  mv opt/paratools/taucmdr-$VERSION .
  tar czf $outdir/$stem.$end.tgz taucmdr-$VERSION
  rm -rf usr taucmdr-$VERSION
  mv $rpmfile $outdir/$stem.$end.rpm
}

function deb2tar()
{
  debfile="$1"
  stem="`echo $debfile | sed -e 's/\.deb//' -e 's/_i[356]86//' -e 's/_x86_64//' -e 's/_amd64//'`"

  case `echo $debfile` in
  *i386*)
    arch=i386
    ;;
  *i586*)
    arch=i586
    ;;
  *i686*)
    arch=i686
    ;;
  *amd64*|*x86_64*)
    arch=amd64
    ;;
  esac

  end=`echo ${distro}_${arch} | sed -e 's/xUbuntu/Ubuntu/'`

  ar x $debfile
  if [ -f "data.tar.gz" ] ; then
    tar xzf data.tar.gz
  elif [ -f "data.tar.xz" ] ; then
    xzcat data.tar.xz | tar xf -
  fi
  mv opt/paratools/taucmdr-$VERSION .
  tar czf $outdir/${stem}_${end}.tgz taucmdr-$VERSION
  rm -rf usr taucmdr-$VERSION control.tar.gz data.tar.gz debian-binary
  mv $debfile $outdir/${stem}_${end}.deb
}

function reprocess()
{
  distro="$1"
  arch="$2"

  if [ -z "$workdir" ] ; then
    workdir="`mktemp -d`"
    pushd $workdir || abort "Failed to change to $workdir"
  fi

  echo "Reprocessing $distro $arch"
  osc getbinaries "$PROJECT" "$PACKAGE" -d . $distro $arch
  pkgfile="`ls taucmdr*.rpm 2>/dev/null`"
  if [ -n "$pkgfile" ] ; then
    rpm2tar $pkgfile
  else
    pkgfile="`ls taucmdr*.deb 2>/dev/null`"
    if [ -n "$pkgfile" ] ; then
      deb2tar $pkgfile
    fi
  fi
}

#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#! Script must be run from OSC package directory
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

re="^(Arch|CentOS|Fedora|RHEL|RedHat|SLE|ScientificLinux|openSUSE|Debian|xUbuntu)"

outdir="$here/reprocessed"
mkdir -p "$outdir"

if [ -n "$1" ] ; then
  reprocess "$1" "$2"
else
  osc getbinaries 2>&1 | egrep "$re" | while read distro arch
  do
    reprocess "$distro" "$arch"
  done
fi

