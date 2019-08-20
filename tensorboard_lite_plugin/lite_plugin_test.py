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
"""Unit tests for the lite plugin."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import collections
import json
import os

import tensorflow as tf

from werkzeug import test as werkzeug_test
from werkzeug import wrappers

from tensorboard.backend import application
from tensorboard.backend.event_processing import plugin_event_multiplexer as event_multiplexer  # pylint: disable=line-too-long
from tensorboard.plugins import base_plugin

from tensorboard_lite_plugin import lite_backend
from tensorboard_lite_plugin import lite_demo_model
from tensorboard_lite_plugin import lite_plugin
from tensorboard_lite_plugin import lite_plugin_loader


class LitePluginTest(tf.test.TestCase):

  def setUp(self):
    super(LitePluginTest, self).setUp()
    logdir = os.path.join(self.get_temp_dir(), "logdir")
    run_logdir = os.path.join(logdir, "0")
    saved_model_dir = os.path.join(logdir, "0", "exported_saved_model")
    model = lite_demo_model.generate_run(run_logdir, saved_model_dir)

    self.input_arrays = lite_demo_model.INPUT_TENSOR_ARRAYS
    self.output_arrays = lite_demo_model.OUTPUT_TENSOR_ARRAYS

    # Create a multiplexer for reading the data we just wrote.
    multiplexer = event_multiplexer.EventMultiplexer()
    multiplexer.AddRunsFromDirectory(logdir)
    multiplexer.Reload()
    context = base_plugin.TBContext(logdir=logdir, multiplexer=multiplexer)

    self.plugin = lite_plugin.LitePlugin(context)
    # TODO(tensorflow/tensorboard#2573): Remove TensorBoardWSGI wrapper.
    wsgi_app = application.TensorBoardWSGI([self.plugin])
    self.server = werkzeug_test.Client(wsgi_app, wrappers.BaseResponse)

    self.routes = self.plugin.get_plugin_apps()

  def _DeserializeResponse(self, byte_content):
    return json.loads(byte_content.decode("utf-8"))

  def test_plugin_is_not_active(self):
    if not lite_backend.is_supported:
      return  # Test conditionally.
    empty_logdir = os.path.join(self.get_temp_dir(), "empty_logdir")
    multiplexer = event_multiplexer.EventMultiplexer()
    multiplexer.AddRunsFromDirectory(empty_logdir)
    multiplexer.Reload()
    context = base_plugin.TBContext(
        logdir=empty_logdir, multiplexer=multiplexer)
    plugin = lite_plugin.LitePlugin(context)
    self.assertFalse(plugin.is_active())

  def test_plugin_is_active(self):
    if not lite_backend.is_supported:
      return  # Test conditionally.
    # The set up for this test generates relevant data.
    self.assertTrue(self.plugin.is_active())
    self.assertTrue(self.plugin.plugin_name, lite_plugin.PLUGIN_PREFIX_ROUTE)

  def test_routes_provided(self):
    self.assertIsInstance(self.routes["/list_supported_ops"],
                          collections.Callable)
    self.assertIsInstance(self.routes["/list_saved_models"],
                          collections.Callable)
    self.assertIsInstance(self.routes["/convert"], collections.Callable)
    self.assertIsInstance(self.routes["/script"], collections.Callable)
    self.assertIsInstance(self.routes["/index.html"], collections.Callable)
    self.assertIsInstance(self.routes["/index.js"], collections.Callable)

  def test_convert_pass(self):
    if not lite_backend.is_supported:
      return  # Test conditionally.
    json_data = json.dumps({
        "input_arrays": self.input_arrays,
        "output_arrays": self.output_arrays,
        "saved_model": os.path.join("0", "exported_saved_model"),
    })
    response = self.server.post(
        "/data/plugin/lite/convert", data={"data": json_data})
    self.assertEqual(200, response.status_code)
    result = self._DeserializeResponse(response.get_data())

    self.assertEqual(result.get("result"), "success")
    self.assertIsNotNone(result.get("tabs"))

  def test_convert_failed(self):
    if not lite_backend.is_supported:
      return  # Test conditionally.
    json_data = json.dumps({
        "input_arrays": self.input_arrays,
        "output_arrays": self.output_arrays,
        "saved_model": "wrong_saved_model",
    })
    response = self.server.post(
        "/data/plugin/lite/convert", data={"data": json_data})
    self.assertEqual(200, response.status_code)
    result = self._DeserializeResponse(response.get_data())
    self.assertEqual(result.get("result"), "failed")
    self.assertIsNotNone(result.get("tabs"))

    json_data = json.dumps({
        "input_arrays": ["wrong_input"],
        "output_arrays": self.output_arrays,
        "saved_model": os.path.join("0", "exported_saved_model"),
    })
    response = self.server.post(
        "/data/plugin/lite/convert", data={"data": json_data})
    self.assertEqual(200, response.status_code)
    result = self._DeserializeResponse(response.get_data())
    self.assertEqual(result.get("result"), "failed")
    self.assertIsNotNone(result.get("tabs"))

  def test_assets(self):
    if not lite_backend.is_supported:
      return  # Test conditionally.
    response = self.server.get("/data/plugin/lite/index.html")
    self.assertTrue(response.get_data())  # Not empty string.

    response = self.server.get("/data/plugin/lite/index.js")
    self.assertTrue(response.get_data())  # Not empty string.

  def test_frontend(self):
    meta = self.plugin.frontend_metadata()
    print(meta)
    self.assertEqual(meta.tab_name, lite_plugin.TAB_NAME)
    self.assertEqual(meta.es_module_path, "/index.js")


if __name__ == "__main__":
  tf.test.main()
