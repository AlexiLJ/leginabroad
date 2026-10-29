import os
from unittest.mock import patch

from django.test import SimpleTestCase

from legin_abroad_base.env_handler import var_getter


class EnvironmentHandlerTests(SimpleTestCase):
    def test_environment_variable_takes_priority(self):
        with patch.dict(os.environ, {"CONTAINER_TEST_VALUE": "from-environment"}):
            self.assertEqual(var_getter("CONTAINER_TEST_VALUE"), "from-environment")

    def test_empty_environment_variable_is_rejected(self):
        with patch.dict(os.environ, {"CONTAINER_TEST_VALUE": ""}):
            with self.assertRaisesRegex(RuntimeError, "set but empty"):
                var_getter("CONTAINER_TEST_VALUE")
