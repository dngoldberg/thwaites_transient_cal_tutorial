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


code_dir=code_oad
strgen="      parameter ( maxCtrlArr2D = $numgen )"
strtim="      parameter ( maxCtrlTim2D = $numtim )"

build_dir=build_$1_oad


cd ../$code_dir
sed "s/.*parameter ( maxCtrlArr2D.*/$strgen/" CTRL_SIZE.h > data.streamice.temp
mv data.streamice.temp CTRL_SIZE.h
sed "s/.*parameter ( maxCtrlTim2D.*/$strtim/" CTRL_SIZE.h > data.streamice.temp
mv data.streamice.temp CTRL_SIZE.h
cd $OLDPWD

long_build_dir=../$build_dir

if [ -d "$long_build_dir" ]; then
  cd $long_build_dir
  rm -rf *
else
  echo 'Creating build directory'
  mkdir $long_build_dir
  cd $long_build_dir
fi

sing_str="-B /exports/geos.ed.ac.uk/iceocean:$HOME -B /scratch:$HOME /scratch/dgoldber/singularity_files/oad_singularity/openad.sif"
optfile=/home/dgoldber/network_links/geosIceOcean/dgoldber/MITgcm_forinput/thwaites_transient_cal_tutorial/scripts/linux_amd64_gfortran_w_petsc
code_dir=/home/dgoldber/network_links/geosIceOcean/dgoldber/MITgcm_forinput/thwaites_transient_cal_tutorial/code_oad

###
make CLEAN
$MITGCM_ROOTDIR/tools/genmake2 -mods=$code_dir -oad --oadsingularity "$sing_str" -of=$optfile -mpi=/usr/bin
#$MITGCM_ROOTDIR/tools/genmake2 -mods=../$code_dir -tap -tap_extra='-defaultnocheckpoint -nooptim adjointliveness' -mpi=/usr/bin -of=../scripts/linux_amd64_gfortran_w_petsc
#make depend
make adAll

