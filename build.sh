#!/bin/sh
# Copyright 2019 The TensorFlow Authors. All Rights Reserved.
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

set -e  # Exit if error.


DIR=`dirname "$0"`

echo "Now building pip..."
python $DIR/setup.py bdist_wheel --python-tag py2

# optional
echo "Now install..."
pip install $DIR/dist/tensorboard_lite_plugin-0.0.1-py2-none-any.whl -U
