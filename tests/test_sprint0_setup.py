import os
import unittest
from unittest.mock import patch

from tests.helpers import NurseryTestCase
from app import ALLOWED_EXTENSIONS, DEFAULT_DEV_SECRET_KEY, allowed_file, load_google_maps_api_key


class Sprint0SetupTests(NurseryTestCase):
    def test_default_secret_key_exists_for_local_development(self):
        self.assertTrue(DEFAULT_DEV_SECRET_KEY)

    def test_allowed_file_accepts_supported_image_extensions(self):
        self.assertTrue(allowed_file("plant.JPG"))
        self.assertTrue(allowed_file("plant.png"))
        self.assertIn("jpeg", ALLOWED_EXTENSIONS)

    def test_allowed_file_rejects_missing_or_unsupported_extension(self):
        self.assertFalse(allowed_file("plant"))
        self.assertFalse(allowed_file("plant.pdf"))

    def test_google_maps_key_falls_back_to_empty_string_when_not_configured(self):
        with patch("app.GOOGLE_MAPS_API_KEY_FILE", "missing-google-key.txt"):
            with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": ""}, clear=False):
                self.assertEqual(load_google_maps_api_key(), "")


if __name__ == "__main__":
    unittest.main()
