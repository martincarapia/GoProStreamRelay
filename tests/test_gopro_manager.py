import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from gopro_manager import GoProManager
import open_gopro
import logging
import asyncio

logging.basicConfig(level=logging.DEBUG)

@pytest.fixture
def log_callback():
    return MagicMock()

@pytest.fixture
def gopro_manager(log_callback):
    return GoProManager(log_callback)

@patch('gopro_manager.WirelessGoPro')
@pytest.mark.asyncio
async def test_setup_gopro_exception(mock_wireless_gopro, gopro_manager, log_callback):
    logging.debug("Starting test_setup_gopro_exception")
    mock_gopro_obj = AsyncMock()
    mock_wireless_gopro.return_value = mock_gopro_obj
    mock_gopro_obj.open.side_effect = Exception("Connection error")

    await gopro_manager.setup_gopro("test_stream", "test_target", "test_ssid", "test_password", "test_server")

    log_callback.assert_any_call("Failed to connect to test_target: Connection error")
    logging.debug("Finished test_setup_gopro_exception")

@patch('gopro_manager.WirelessGoPro')
@pytest.mark.asyncio
async def test_stop_live_stream_success(mock_wireless_gopro, gopro_manager, log_callback):
    mock_gopro_obj = AsyncMock()
    mock_wireless_gopro.return_value = mock_gopro_obj

    await gopro_manager.stop_live_stream("test_target")

    mock_gopro_obj.open.assert_called_once_with(retries=100)
    mock_gopro_obj.ble_command.set_shutter.assert_called_with(shutter=open_gopro.Params.Toggle.DISABLE)
    mock_gopro_obj.close.assert_called_once()
    log_callback.assert_any_call("test_target: Livestream has been stopped.")

@patch('gopro_manager.requests.get')
def test_run_script_on_server_success(mock_requests_get, gopro_manager, log_callback):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "Script executed successfully"
    mock_requests_get.return_value = mock_response

    gopro_manager.run_script_on_server("test_script.py", "run", "test_server")

    mock_requests_get.assert_called_once_with('http://test_server:8080?script_path=test_script.py&action=run')
    log_callback.assert_any_call("Script output: Script executed successfully")

@patch('gopro_manager.requests.get')
def test_run_script_on_server_exception(mock_requests_get, gopro_manager, log_callback):
    mock_requests_get.side_effect = Exception("Connection error")

    gopro_manager.run_script_on_server("test_script.py", "run", "test_server")

    log_callback.assert_any_call("Failed to connect to server: Connection error")