from unittest.mock import patch
import os
import tempfile
from click.testing import CliRunner

from cos.commands.sync import sync


def test_sync_local_to_cos_with_flags_no_progress(tmp_path):
    # Create local dir with a file
    d = tmp_path / "src"
    d.mkdir()
    f = d / "a.txt"
    f.write_text("hello")

    runner = CliRunner()

    with patch('cos.commands.sync.ConfigManager') as mock_cfg, \
         patch('cos.commands.sync.COSAuthenticator') as mock_auth, \
         patch('cos.commands.sync.COSClient') as mock_client_class:
        mock_client = mock_client_class.return_value
        result = runner.invoke(sync, [
            str(d),
            'cos://bucket/prefix/',
            '--no-progress', '--part-size', '1MB', '--max-retries', '2', '--retry-backoff', '0.1', '--retry-backoff-max', '0.5'
        ], obj={"profile": "default"})
        assert result.exit_code == 0
        # Should attempt upload
        assert mock_client.upload_file.called
