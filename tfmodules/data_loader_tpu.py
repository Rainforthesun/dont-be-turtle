# Copyright 2018 Jaewook Kang (jwkang10@gmail.com) All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
# -*- coding: utf-8 -*-

"""Efficient dont be turtle input pipeline using tf.data.Dataset."""
# code ref: https://github.com/tensorflow/tpu/blob/1fe0a9b8b8df3e2eb370b0ebb2f80eded6a9e2b6/models/official/resnet/imagenet_input.py

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import sys
import tensorflow as tf
import functools
from glob import glob
from path_manager import TF_MODULE_DIR
from path_manager import TF_MODEL_DIR

sys.path.insert(0,TF_MODULE_DIR)
sys.path.insert(0,TF_MODEL_DIR)

from train_config  import FLAGS
from train_config  import BATCH_SIZE
from train_config  import TRAININGSET_SIZE
from train_config  import VALIDATIONSET_SIZE
from model_config  import DEFAULT_INPUT_RESOL


import preprocessor


DEFAULT_HEIGHT = DEFAULT_INPUT_RESOL
DEFAULT_WIDTH  = DEFAULT_INPUT_RESOL


def image_serving_input_fn():
    """Serving input fn for raw images.
    """

    def _preprocess_image(image_bytes,
                          label_bytes_list,
                          image_orig_height,
                          image_orig_width):
        """Preprocess a single raw image."""
        image = preprocessor.preprocess_image(
            image_bytes         =image_bytes,
            label_bytes_list    =label_bytes_list,
            image_orig_height   =image_orig_height,
            image_orig_width    =image_orig_width,
            is_training         =False)

        return image

    image_bytes  = tf.placeholder(shape=[None],
                                  dtype=tf.string)

    label_head_bytes      = tf.placeholder(shape=[None],dtype=tf.string)
    label_neck_bytes      = tf.placeholder(shape=[None],dtype=tf.string)
    label_Rshoulder_bytes = tf.placeholder(shape=[None],dtype=tf.string)
    label_Lshoulder_bytes = tf.placeholder(shape=[None],dtype=tf.string)

    image_height          = tf.placeholder(shape=[None],dtype=tf.int32)
    image_width           = tf.placeholder(shape=[None],dtype=tf.int32)

    label_byte_list = [label_head_bytes,
                       label_neck_bytes,
                       label_Rshoulder_bytes,
                       label_Lshoulder_bytes]


    images = tf.map_fn(fn=_preprocess_image,
                       elems=(image_bytes,
                              label_byte_list,
                              image_height,
                              image_width),
                       back_prop=False,
                       dtype=tf.float32)

    return tf.estimator.export.ServingInputReceiver(
      images, {'image_bytes': image_bytes,
               'label_head_bytes': label_head_bytes,
               'label_neck_bytes': label_neck_bytes,
               'label_Rshoulder': label_Rshoulder_bytes,
               'label_Lshoulder': label_Lshoulder_bytes,
               'image_height':    image_height,
               'imaeg_width':     image_width})





class DataSetInput(object):
    """Generates DataSet input_fn for training or evaluation
        The training data is assumed to be in TFRecord format with keys as specified
        in the dataset_parser below, sharded across 1024 files, named sequentially:

            train-00000-of-01024
            train-00001-of-01024
            ...
            train-01023-of-01024

        The validation data is in the same format but sharded in 128 files.

        The format of the data required is created by the script at:
        https://github.com/tensorflow/tpu/blob/master/tools/datasets/imagenet_to_gcs.py

        Args:
            is_training: `bool` for whether the input is for training
            data_dir:   `str` for the directory of the training and validation data;
                            if 'null' (the literal string 'null', not None), then construct a null
                            pipeline, consisting of empty images.
            use_bfloat16: If True, use bfloat16 precision; else use float32.
            transpose_input: 'bool' for whether to use the double transpose trick
    """

    def __init__(self, is_training,
                 data_dir,
                 use_bfloat16,
                 transpose_input=True):

        self.image_preprocessing_fn = preprocessor.preprocess_image
        self.is_training            = is_training
        self.use_bfloat16           = use_bfloat16
        self.data_dir               = data_dir

        if self.data_dir == 'null' or self.data_dir == '':
            self.data_dir = None
        self.transpose_input = transpose_input






    def set_shapes(self, batch_size,
                         images,
                         labels):
        """Statically set the batch_size dimension."""

        # if FLAGS.use_tpu == True and self.transpose_input:
        #     images.set_shape(images.get_shape().merge_with
        #     (tf.TensorShape([None, None, None, batch_size])))
        #
        #     labels.set_shape(labels.get_shape().merge_with
        #     (tf.TensorShape([None,None,None,batch_size])))
        #
        # else:
        images.set_shape(images.get_shape().merge_with(
          tf.TensorShape([batch_size, None, None, None])))

        # below codes must be modified after applying preprocessing
        labels.set_shape(labels.get_shape().merge_with(
            tf.TensorShape([batch_size, None,None,None])))

        return images, labels






    def dataset_parser(self, value):
        """Parse an dont be turtle TFrecord from a serialized string Tensor."""
        keys_to_features = {
            'height':
                tf.FixedLenFeature((), dtype=tf.int64, default_value=0),
            'width':
                tf.FixedLenFeature((), dtype=tf.int64, default_value=0),
            'channel':
                tf.FixedLenFeature((), dtype=tf.int64, default_value=3),
            'image':
                tf.FixedLenFeature((), dtype=tf.string, default_value=""),
            'label_head_x':
                tf.FixedLenFeature([], dtype=tf.int64, default_value=0),
            'label_head_y':
                tf.FixedLenFeature([], dtype=tf.int64, default_value=0),
            'label_head_occ':
                tf.FixedLenFeature([], dtype=tf.int64, default_value=0),
            'label_neck_x':
                tf.FixedLenFeature([], dtype=tf.int64, default_value=0),
            'label_neck_y':
                tf.FixedLenFeature([], dtype=tf.int64, default_value=0),
            'label_neck_occ':
                tf.FixedLenFeature([], dtype=tf.int64, default_value=0),
            'label_Rshoulder_x':
                tf.FixedLenFeature([], dtype=tf.int64, default_value=0),
            'label_Rshoulder_y':
                tf.FixedLenFeature([], dtype=tf.int64, default_value=0),
            'label_Rshoulder_occ':
                tf.FixedLenFeature([], dtype=tf.int64, default_value=0),
            'label_Lshoulder_x':
                tf.FixedLenFeature([], dtype=tf.int64, default_value=0),
            'label_Lshoulder_y':
                tf.FixedLenFeature([], dtype=tf.int64, default_value=0),
            'label_Lshoulder_occ':
                tf.FixedLenFeature([], dtype=tf.int64, default_value=0),
            'mean':
                tf.VarLenFeature(dtype=tf.float32),
            'std':
                tf.VarLenFeature(dtype=tf.float32),
            "filename":
                tf.FixedLenFeature([], tf.string, default_value="")
        }

        parsed = tf.parse_single_example(serialized =value,
                                         features   =keys_to_features)
        # images
        image_bytes = tf.reshape(parsed['image'], shape=[])

        # labels
        label_head_x        = tf.cast(parsed['label_head_x'], dtype=tf.float32)
        label_head_y        = tf.cast(parsed['label_head_y'], dtype=tf.float32)
        label_head_occ      = tf.cast(parsed['label_head_occ'], dtype=tf.int32)

        label_neck_x        = tf.cast(parsed['label_neck_x'], dtype=tf.float32)
        label_neck_y        = tf.cast(parsed['label_neck_y'], dtype=tf.float32)
        label_neck_occ      = tf.cast(parsed['label_neck_occ'], dtype=tf.int32)

        label_Rshoulder_x        = tf.cast(parsed['label_Rshoulder_x'], dtype=tf.float32)
        label_Rshoulder_y        = tf.cast(parsed['label_Rshoulder_y'], dtype=tf.float32)
        label_Rshoulder_occ      = tf.cast(parsed['label_Rshoulder_occ'], dtype=tf.int32)

        label_Lshoulder_x        = tf.cast(parsed['label_Lshoulder_x'], dtype=tf.float32)
        label_Lshoulder_y        = tf.cast(parsed['label_Lshoulder_y'], dtype=tf.float32)
        label_Lshoulder_occ      = tf.cast(parsed['label_Lshoulder_occ'], dtype=tf.int32)

        label_head_list = [label_head_x,
                           label_head_y,
                           label_head_occ]

        label_neck_list = [label_neck_x,
                           label_neck_y,
                           label_neck_occ]

        label_Rshoulder_list = [label_Rshoulder_x,
                                label_Rshoulder_y,
                                label_Rshoulder_occ]

        label_Lshoulder_list = [label_Lshoulder_x,
                                label_Lshoulder_y,
                                label_Lshoulder_occ]

        label_list = [label_head_list,
                      label_neck_list,
                      label_Rshoulder_list,
                      label_Lshoulder_list]


        # get the original image shape
        height      = tf.cast(parsed['height']  ,dtype=tf.int32)
        width       = tf.cast(parsed['width']   ,dtype=tf.int32)
        channel     = tf.cast(parsed['channel'] ,dtype=tf.int32)
        mean        = parsed['mean']
        std         = parsed['std']

        # preprocessing
        image,label_heatmap = self.image_preprocessing_fn(
                                    image_bytes         =image_bytes,
                                    image_orig_height   =height,
                                    image_orig_width    =width,
                                    label_list          =label_list,
                                    is_training         =self.is_training,
                                    use_bfloat16        =self.use_bfloat16)


        return image, label_heatmap






    def input_fn(self, params=None):
        """Input function which provides a single batch for train or eval.
            Args:
                params: `dict` of parameters passed from the `TPUEstimator`.
                  `params['batch_size']` is always provided and should be used as the
                  effective batch size.
            Returns:
                A `tf.data.Dataset` object.

            doc reference: https://www.tensorflow.org/api_docs/python/tf/data/TFRecordDataset
        """

        if self.data_dir == None:
            tf.logging.info('Using fake input.')
            return self.input_fn_null(params)

        # Retrieves the batch size for the current shard. The # of shards is
        # computed according to the input pipeline deployment. See
        # tf.contrib.tpu.RunConfig for details.

        batch_size = BATCH_SIZE

        # loading tfrecord filenames from self.data_dir
        if self.is_training:
            # training set
            filenames_list = glob(self.data_dir + '/train-*.*')
        else:
            # validation set
            filenames_list = glob(self.data_dir + '/eval-*.*')

        dataset = tf.data.TFRecordDataset(filenames_list)

        print('\nfile_pattern=%s'%filenames_list)

        # compression_type = 'ZLIB' if filenames_list[0].split('.')[-1] == 'zlib' else 'GZIP'
        # -----------------------------------------------------------------

        # Shuffle the filenames to ensure better randomization.
        # file_pattern = os.path.join(
        #     self.data_dir, 'train-*' if self.is_training else 'eval-*')
        #
        # print('file_pattern=%s'%file_pattern)
        # dataset = tf.data.Dataset.list_files(file_pattern,
        #                                      shuffle=self.is_training)

        if self.is_training:
            dataset = dataset.repeat()

        # loading dataset from tfrecords files
        # def fetch_dataset(filename):
        #     # dataset = tf.data.TFRecordDataset(filename,
        #     #                                   compression_type='GZIP')
        #     print ('filename=%s'%filename)
        #     dataset = tf.data.TFRecordDataset(filename)
        #     return dataset

        # Read the data from disk in parallel
        # dataset = dataset.apply(
        #     tf.contrib.data.parallel_interleave(
        #         fetch_dataset, cycle_length=32, sloppy=True))

        # dataset elementwise shuffling
        # where buffer_size is the number of data elements
        if self.is_training:
            dataset = dataset.shuffle(buffer_size=TRAININGSET_SIZE)
        else:
            dataset = dataset.shuffle(buffer_size=VALIDATIONSET_SIZE)


        # if FLAGS.use_tpu:
        #     # # Parse, preprocess, and batch the data in parallel
        #     dataset = dataset.apply(
        #         tf.contrib.data.map_and_batch(map_func=self.dataset_parser,
        #                                       batch_size=batch_size,
        #                                       num_parallel_batches=8,  # 8 == num_cores per host
        #                                       drop_remainder=True))
        #
        # else:
        # Parse, preprocess, and batch the data in parallel
        dataset = dataset.apply(
            tf.contrib.data.map_and_batch(map_func=self.dataset_parser,
                                          batch_size=batch_size,
                                          drop_remainder=True))


        ########################################
        # Transpose for performance on TPU
        # if FLAGS.use_tpu == True and self.transpose_input:
        #     dataset = dataset.map(
        #       lambda images, labels: (tf.transpose(images, [1, 2, 3, 0]), labels),
        #       num_parallel_calls=8)
        ########################################


        # Assign static batch size dimension
        dataset = dataset.map(functools.partial(self.set_shapes, batch_size))

        # Prefetch overlaps in-feed with training
        dataset = dataset.prefetch(tf.contrib.data.AUTOTUNE)

        ########################################
        # here we can return "object of TFRecordDataset" or iterator().get_next()
        # there is some performance difference between them but currently ignorable
        # iterator = dataset.make_initializable_iterator()
        # a = iterator.get_next()
        ########################################

        return dataset





    def input_fn_null(self, params):
        """Input function which provides null (black) images."""
        batch_size = BATCH_SIZE
        dataset = tf.data.Dataset.range(1).repeat().map(self._get_null_input)
        dataset = dataset.prefetch(batch_size)

        dataset = dataset.apply(
            tf.contrib.data.batch_and_drop_remainder(batch_size))
        # if FLAGS.use_tpu == True and self.transpose_input:
        #   dataset = dataset.map(
        #       lambda images, labels: (tf.transpose(images, [1, 2, 3, 0]), labels),
        #       num_parallel_calls=8)

        dataset = dataset.map(functools.partial(self.set_shapes, batch_size))

        dataset = dataset.prefetch(batch_size)     # Prefetch overlaps in-feed with training
        tf.logging.info('Input dataset: %s', str(dataset))
        return dataset






    def _get_null_input(self, _):
        null_image = tf.zeros(shape=[DEFAULT_HEIGHT, DEFAULT_WIDTH, 3],
                              dtype=tf.bfloat16 if self.use_bfloat16
                              else tf.float32)
        return (null_image, tf.constant(0, tf.int32))

