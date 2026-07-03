ROOTDIR=/scratch/dgoldber/MITgcm

if [ $1 == "genarr" ]; then
        numgen=3
        numtim=0
elif [ $1 == "snap" ]; then 
        numgen=2
        numtim=0
elif [ $1 == "gentim" ]; then
        numgen=0
        numtim=3
fi


code_dir=code
strgen="      parameter ( maxCtrlArr2D = $numgen )"
strtim="      parameter ( maxCtrlTim2D = $numtim )"

build_dir=build_$1_tap


cd ../$code_dir
sed "s/.*parameter ( maxCtrlArr2D.*/$strgen/" CTRL_SIZE.h > data.streamice.temp
mv data.streamice.temp CTRL_SIZE.h
sed "s/.*parameter ( maxCtrlTim2D.*/$strtim/" CTRL_SIZE.h > data.streamice.temp
mv data.streamice.temp CTRL_SIZE.h
cd $OLDPWD


if [ -d "../$build_dir" ]; then
  cd ../$build_dir
  rm -rf *
else
  echo 'Creating build directory'
  mkdir ../$build_dir
  cd ../$build_dir
fi

# if  you are not using PETSC, you can comment these
#PETSCDIR='/scratch/dgoldber/petsc-3.14.2/'
#ln -s $PETSCDIR/arch-linux-c-opt/include/*.mod .
echo $LD_LIBRARY_PATH
###
make CLEAN
#$ROOTDIR/tools/genmake2 -mods=../$code_dir -of=$HOME/own_scripts/dev_linux_amd64_cray_archer2_oad -tap -mpi -tap_extra='-defaultnocheckpoint -nooptim adjointliveness' 
$ROOTDIR/tools/genmake2 -mods=../$code_dir -tap -tap_extra='-defaultnocheckpoint -nooptim adjointliveness' -rootdir=$ROOTDIR -mpi=/usr/bin -of=../scripts/linux_amd64_gfortran_w_petsc
make depend
echo $LD_LIBRARY_PATH
make -j tap_adj

