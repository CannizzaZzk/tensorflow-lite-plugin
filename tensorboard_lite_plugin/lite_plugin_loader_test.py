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
"""Integration tests for the lite_plugin_loader."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


import tensorflow as tf

from tensorboard.backend.event_processing import plugin_event_multiplexer as event_multiplexer  # pylint: disable=line-too-long
from tensorboard.plugins import base_plugin

from tensorboard_lite_plugin import lite_backend
from tensorboard_lite_plugin import lite_plugin
from tensorboard_lite_plugin import lite_plugin_loader


class LitePluginLoaderTest(tf.test.TestCase):

  def setUp(self):
    super(LitePluginLoaderTest, self).setUp()
    multiplexer = event_multiplexer.EventMultiplexer()
    self.context = base_plugin.TBContext(multiplexer=multiplexer)
    # Keep state.
    self.old_is_supported = lite_backend.is_supported

  def tearDown(self):
    # Resume state.
    lite_backend.is_supported = self.old_is_supported

  def test_load_if_supported(self):
    lite_backend.is_supported = True
    plugin = lite_plugin_loader.LitePluginLoader().load(self.context)
    self.assertIsNotNone(plugin)
    self.assertIsInstance(plugin, lite_plugin.LitePlugin)

  def test_load_if_not_supported(self):
    lite_backend.is_supported = False
    plugin = lite_plugin_loader.LitePluginLoader().load(self.context)
    self.assertIsNone(plugin)


if __name__ == '__main__':
  tf.test.main()
