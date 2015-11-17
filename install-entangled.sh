#!/bin/bash
set -e

#entangled=entangled-0.1
#tar=${entangled}.tar.gz
#if [ ! -d $entangled ]; then
#    [ ! -f $tar ] && wget http://downloads.sourceforge.net/project/entangled/entangled/0.1/$tar
#    tar xzf $tar
#fi
#
#prevdir=`pwd`
#cd $entangled
#sudo python setup.py install
#cd $prevdir
#
#rm $tar
#rm -r $entangled

prevdir=`pwd`
svn checkout svn://svn.code.sf.net/p/entangled/code/ /tmp/entangled-code
cd /tmp/entangled-code/entangled
sudo python setup.py install
cd $prevdir
