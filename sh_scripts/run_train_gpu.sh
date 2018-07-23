#! /bin/bash

echo =============================================
echo RUN DONBE-TURTLE-MODEL TRAINING  BY GPU
echo JAEWOOK KANG JEJU GOOGLE CAMP 2018
echo =============================================

echo "       _                 _         "
echo " _   _| |__  _   _ _ __ | |_ _   _ "
echo "| | | | '_ \| | | | '_ \| __| | | |"
echo "| |_| | |_) | |_| | | | | |_| |_| |"
echo " \__,_|_.__/ \__,_|_| |_|\__|\__,_|"



echo "  .------------------------."
echo "  |  Hi ! Google Camp 2018 |"
echo "  '------------------------'"
echo "      ^      (\_/)"
echo "      '----- (O.o)"
echo "             (> <)"
OS="$(uname -s)"
OS_X="Darwin"

echo ${OS}

if [ "$OS" == "$OS_X" ]; then
    export MODEL_BUCKET=/Users/jwkangmacpro2/SourceCodes/dont-be-turtle/tfmodules/export/model/
    export DATA_BUCKET=/Users/jwkangmacpro2/SourceCodes/dont-be-turtle/dataset/tfrecords/realdataset/
    export SOURCE=~/SourceCodes/dont-be-turtle/tfmodules/trainer_gpu.py
else
    rm -rf /tmp/gcs_filesystem*
#    export MODEL_BUCKET=/Users/jwkangmacpro2/SourceCodes/dont-be-turtle/tfmodules/export/model
    export MODEL_BUCKET=gs://dontbeturtle_ckpt3
    export TENSORBOARD_BUCKET=gs://dontbeturtle_tflogs3
    export DATA_BUCKET=/home/jwkangmacpro2/dont-be-turtle/dataset/tfrecords/realdataset
#    export DATA_BUCKET=null
    export SOURCE=~/dont-be-turtle/tfmodules/trainer_gpu.py
fi


echo "MODEL_BUCKET="${MODEL_BUCKET}
echo "DATA_BUCKET="${DATA_BUCKET}
echo =============================================

python ${SOURCE}\
  --data_dir=${DATA_BUCKET}\
  --model_dir=${MODEL_BUCKET}\
  --tflogs_dir=${TENSORBOARD_BUCKET}



