#
#

#nprocs=128
itermax=5
procsonnode=20


#

name=optiter
echo "Beginning of script"
ite=`egrep 'optimcycle' data.optim | sed 's/ optimcycle=//'| sed 's/,$//'`
i=`expr $ite + 1`

echo "Beginning of script"

mkdir gradcontrol

while [ $i -le $itermax ];
do
 ii=`./add0upto3c $i`
 echo "Beginning of iteration $ii"
 cp OPTIM/ecco_ctrl_MIT_CE_000.opt0$ii .
 ite=`expr $i - 1`
 sed "s/ optimcycle=$ite/ optimcycle=$i/" data.optim > TTT.tmp
 mv -f TTT.tmp data.optim
 fich=output$name$ii
 echo "Running mitcgm_ad: iteration $ii"
 mpirun -n $procsonnode ./mitgcmuv_tap_adj > out 2> err
 mv STDOUT.0000 $fich
 egrep optimcycle data.optim >> fcost$name
 grep "objf_temp_tut(" $fich >> fcost$name
 grep "objf_hflux_tut(" $fich >> fcost$name
 egrep 'global fc =' $fich >> fcost$name
 grep 'global fc =' $fich
 echo Cleaning
 mv adxx* gradcontrol
 mv xx*ta gradcontrol
 if [ $((i % 1)) -eq 0 ]; then 
  direc=run$name$ii
  mkdir $direc
  rm maskCtrl* hFac* wunit* RA*ta DX*ta DY*ta DR*ta PH*ta
  mv -f *.meta *.data STDOUT* STDERR* out err $direc 
  mv -f $direc/wunit*.*data ./
 fi
 cp -f ecco_ctrl_MIT_CE_000.opt0$ii OPTIM/
 cp -f ecco_cost_MIT_CE_000.opt0$ii OPTIM/
 echo "Line-search: iteration $ii"
 cd OPTIM/
 egrep optimcycle data.optim
 cp -f ../data.optim .
 ./optim.x > std$ii
 cd ..

 i=`expr $i + 1`
done

rm ecco_c*

exit

echo "DONE WITH OPT"

#for i in $(ls -d runoptiter*00); do 
# mv $i SAVE$i;
#done
#rm OPTIM/OPWARM*



#----------------------------------------------------

# --- end of script ---
