import logging
import tempfile
from unittest import TestCase, mock, skip
from unittest.mock import Mock
from botocore.exceptions import ClientError

from kg_obo.transform import run_transform, kgx_transform


class TestRunTransform(TestCase):

    def setUp(self) -> None:
        self.kgx_transform_kwargs = {'input_file': ['foo'], 'input_format': 'tsv',
                                     'output_file': 'bar', 'output_format': 'tsv',
                                     'logger': logging.Logger}

    @mock.patch('requests.get')
    @mock.patch('kg_obo.transform.retrieve_obofoundry_yaml')
    @mock.patch('kg_obo.obolibrary_utils.base_url_if_exists')
    @mock.patch('kgx.cli.transform')
    def test_run_transform(self, mock_kgx_transform, mock_base_url,
                           mock_retrieve_obofoundry_yaml, mock_get):
        with tempfile.TemporaryDirectory() as td:
            mock_retrieve_obofoundry_yaml.return_value = [{'id': 'bfo'}]
            ret_val = run_transform(log_dir=td)
            self.assertTrue(mock_get.called)
            self.assertTrue(mock_base_url.called)
            self.assertTrue(mock_retrieve_obofoundry_yaml.called)
            self.assertTrue(mock_kgx_transform.called)

    @mock.patch('kgx.cli.transform')
    def test_kgx_transform(self, mock_kgx_transform) -> None:
        ret_val = kgx_transform(**self.kgx_transform_kwargs)
        self.assertTrue(mock_kgx_transform.called)
        self.assertTrue(ret_val)

        mock_kgx_transform.side_effect = Exception(mock.Mock())
        mock_kgx_transform.side_effect.isEnabledFor = mock.Mock()
        mock_kgx_transform.side_effect._log = mock.Mock()
        ret_val = kgx_transform(**self.kgx_transform_kwargs)
        self.assertTrue(mock_kgx_transform.called)
        self.assertFalse(ret_val)
