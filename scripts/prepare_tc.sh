#!/bin/bash

if [[ -z ${1:-} ]]; then
    echo "Missing argument: 'oad' or 'tap'"
    exit 1
elif [[ $1 == "tap" || $1 == "oad" ]]; then
    echo "Valid argument: $1"
else
    echo "Invalid argument: $1"
    exit 1
fi

run_folder=run_tc_$1
echo $run_folder
if [ -d "../$run_folder" ]; then
  cd ../$run_folder
  rm -rf *
else
  mkdir ../$run_folder
  cd ../$run_folder
fi

inputdir=input

ln -s ../$inputdir/*bin .
ln -s ../$inputdir/data* .
ln -s data.streamice_gentim data.streamice
ln -s data.ctrl_gentim data.ctrl
ln -s ../$inputdir/eedata .
rm data
cp ../input/data ./
strtimestep=" nTimesteps=96,"
sed "s/.*nTimesteps=.*/$strtimestep/" data > temp
mv temp data

ln -s ../input/velocity_constraints .
ln -s ../input/surface_constraints .

builddir=build_gentim_$1
ln -s ../${builddir}/mitgcmuv_ad .

ln -s ../scripts/add0upto3c .
ln -s ../scripts/clear_optim.sh .
mkdir OPTIM
cd ../optim_m1qn3/src
bash prep_make ../../$builddir
make clean
make depend
make;
cp optim.x $OLDPWD/OPTIM
cd $OLDPWD/OPTIM
ln -s ../data.optim .
ln -s ../data.ctrl .
cd ../
cp ../scripts/opt_script.csh ./
./clear_optim.sh
