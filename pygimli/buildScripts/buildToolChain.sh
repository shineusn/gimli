#!/usr/bin/env bash

if [ $# -eq 0 ]; then
	prefix=`pwd`
else 
	prefix=`readlink -m $1`
fi

echo "Installing at " $prefix

GCCXML_BIN_ROOT=$prefix/gccxml-bin

echo "looking for gcc ..."
if ( (gcc --version) );then
	echo "... found, good"
else
	echo "need a working gcc installation"
	exit
fi
echo ""
echo "looking for python ..."
if ( (python --version) );then
	echo "... found, good"
else
	echo "need python2.6 installation"
	echo "get one from http://www.python.org/"
	echo "if allready ensure python26 installation directory is in your PATH"
	exit
fi
echo ""
echo "looking for cmake ..."
if ( (cmake --version) );then
	echo "... found, good"
else
	echo "need cmake"
	echo "get one from http://www.cmake.org/cmake/resources/software.html"
	echo "if allready ensure cmake installation directory is in your PATH"
	exit
fi
echo ""
echo "looking for svn ..."
if ( (svn --version --quiet) );then
	echo "... found, good"
else
	echo "need svn client"
	echo "get one from http://www.sliksvn.com/en/download"
	echo "if allready ensure svn installation directory is in your PATH"
	exit
fi
echo ""
echo "Installing sources at" $prefix

installGCCXML(){
    echo "install gccxml"
    pushd $prefix
		cvs -d :pserver:anoncvs@www.gccxml.org:/cvsroot/GCC_XML co gccxml/
		rm -rf gccxml-build gccxml-bin
		mkdir -p gccxml-build
		mkdir -p $GCCXML_BIN_ROOT
		pushd gccxml-build
			cmake -D CMAKE_INSTALL_PREFIX=$GCCXML_BIN_ROOT ../gccxml -G 'MSYS Makefiles' 
			make
			make install
		popd
	popd
}

fixGCCXML(){
	GCCXML_CFG=$GCCXML_BIN_ROOT/share/gccxml-0.9/gccxml_config
	pushd $prefix
		rm -rf *.gch
		echo "#include <string>" > test.h
		("$GCCXML_BIN_ROOT/bin/gccxml" --debug test.h > .test.log)

		
		if [ $? -gt 0 ]; then
			echo "gccxml test fail"
			USER_FLAGS=''
			#-isystemc:mingw_w64bin
			for i in `grep "isystemc:" .test.log | sed -e 's/isystemc:mingw/isystemc:\/mingw/' | sed -e 's/bin../\/bin\/../' | tr -s '"' '\ '`; do
			#for i in `grep "isystemc:" .test.log | sed -e 's/isystemc:mingwbin../isystemc:\/mingw\/bin\/../' | tr -s '"' '\ '`; do
				echo $i
				USER_FLAGS=$USER_FLAGS' '$i
			done
			echo -e 'GCCXML_USER_FLAGS="'$USER_FLAGS'"' >> "$GCCXML_CFG"
			echo "I will now try to fix this gccxml installation ... "
			echo "You may rerun this test. If this error occur please contact me. Carsten."
		else
			echo "gccxml seems to work"
		fi
		#rm -rf test.h .test.log
    popd
}
#WORKING_PYGCC_REV=1842
WORKING_PYGCC_REV=1856

installPYGCCXML(){
    echo "install pygccxml"
    pushd $prefix
        echo "getting sources ..."
        svn co https://pygccxml.svn.sourceforge.net/svnroot/pygccxml/pygccxml_dev -r $WORKING_PYGCC_REV pygccxml
        pushd pygccxml
            python setup.py install
        popd
    popd
}

installPYPLUSPLUS(){
    echo "install pyplusplus"
    pushd $prefix
        echo "getting sources ..."
        svn co https://pygccxml.svn.sourceforge.net/svnroot/pygccxml/pyplusplus_dev -r $WORKING_PYGCC_REV pyplusplus
        pushd pyplusplus
            python setup.py install
        popd
    popd
}

installGCCXML
installPYGCCXML
installPYPLUSPLUS
fixGCCXML
fixGCCXML