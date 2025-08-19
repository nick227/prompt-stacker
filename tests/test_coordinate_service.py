"""
Unit tests for CoordinateCaptureService.

Tests the coordinate capture functionality for the automation system.
"""

from unittest.mock import Mock, patch

import pytest

from coordinate_service import CoordinateCaptureService


class TestCoordinateCaptureService:
    """Test cases for CoordinateCaptureService."""

    @pytest.fixture
    def service(self):
        """Create a fresh service instance for each test."""
        with patch("coordinate_service.load_coords", return_value={}):
            return CoordinateCaptureService()

    @pytest.mark.unit
    def test_init(self, service):
        """Test service initialization."""
        assert service.coords == {}
        assert service.capture_active is False
        assert service.capture_key is None
        assert service.listener is None
        assert service.on_coord_captured is None

    @pytest.mark.unit
    def test_get_coordinates(self, service, sample_coordinates):
        """Test getting coordinates."""
        service.coords = sample_coordinates.copy()
        coords = service.get_coordinates()

        assert coords == sample_coordinates
        assert coords is not service.coords  # Should be a copy

    @pytest.mark.unit
    def test_set_coordinate(self, service):
        """Test setting a coordinate."""
        with patch("coordinate_service.save_coords") as mock_save:
            service.set_coordinate("input", (100, 200))

            assert service.coords["input"] == (100, 200)
            mock_save.assert_called_once_with(service.coords)

    @pytest.mark.unit
    def test_has_coordinate_true(self, service):
        """Test checking for existing coordinate."""
        service.coords["input"] = (100, 200)
        assert service.has_coordinate("input") is True

    @pytest.mark.unit
    def test_has_coordinate_false(self, service):
        """Test checking for non-existing coordinate."""
        assert service.has_coordinate("input") is False

    @pytest.mark.unit
    def test_get_coordinate_exists(self, service):
        """Test getting existing coordinate."""
        service.coords["input"] = (100, 200)
        coord = service.get_coordinate("input")

        assert coord == (100, 200)

    @pytest.mark.unit
    def test_get_coordinate_not_exists(self, service):
        """Test getting non-existing coordinate."""
        coord = service.get_coordinate("input")
        assert coord is None

    @pytest.mark.unit
    def test_clear_coordinate(self, service):
        """Test clearing a specific coordinate."""
        with patch("coordinate_service.save_coords") as mock_save:
            service.coords = {"input": (100, 200), "submit": (300, 400)}
            service.clear_coordinate("input")

            assert "input" not in service.coords
            assert "submit" in service.coords
            mock_save.assert_called_once()

    @pytest.mark.unit
    def test_remove_coordinate(self, service):
        """Test removing a coordinate."""
        with patch("coordinate_service.save_coords") as mock_save:
            service.coords["input"] = (100, 200)
            result = service.remove_coordinate("input")

            assert result is True
            assert "input" not in service.coords
            mock_save.assert_called_once()

    @pytest.mark.unit
    def test_remove_coordinate_not_exists(self, service):
        """Test removing non-existing coordinate."""
        result = service.remove_coordinate("input")
        assert result is False

    @pytest.mark.unit
    def test_start_capture_success(self, service):
        """Test successful capture start."""
        with patch("coordinate_service.mouse.Listener") as mock_listener_class:
            mock_listener = Mock()
            mock_listener_class.return_value = mock_listener

            result = service.start_capture("input")

            assert result is True
            assert service.capture_active is True
            assert service.capture_key == "input"
            assert service.listener == mock_listener
            mock_listener.start.assert_called_once()

    @pytest.mark.unit
    def test_start_capture_already_active(self, service):
        """Test starting capture when already active."""
        service.capture_active = True
        result = service.start_capture("input")
        assert result is False

    @pytest.mark.unit
    def test_start_capture_invalid_key(self, service):
        """Test starting capture with invalid key."""
        result = service.start_capture("invalid")
        assert result is False

    @pytest.mark.unit
    def test_stop_capture_success(self, service):
        """Test successful capture stop."""
        mock_listener = Mock()
        service.listener = mock_listener
        service.capture_active = True
        service.capture_key = "input"

        service.stop_capture()

        assert service.capture_active is False
        assert service.capture_key is None
        assert service.listener is None
        mock_listener.stop.assert_called_once()

    @pytest.mark.unit
    def test_stop_capture_not_active(self, service):
        """Test stopping capture when not active."""
        service.stop_capture()  # Should not raise error
        assert service.capture_active is False

    @pytest.mark.unit
    def test_is_capturing_true(self, service):
        """Test checking if capturing when active."""
        service.capture_active = True
        assert service.is_capturing() is True

    @pytest.mark.unit
    def test_is_capturing_false(self, service):
        """Test checking if capturing when not active."""
        service.capture_active = False
        assert service.is_capturing() is False

    @pytest.mark.unit
    def test_get_capture_key(self, service):
        """Test getting capture key."""
        service.capture_key = "input"
        key = service.get_capture_key()
        assert key == "input"

    @pytest.mark.unit
    def test_get_capture_key_none(self, service):
        """Test getting capture key when none set."""
        key = service.get_capture_key()
        assert key is None

    @pytest.mark.unit
    def test_set_callback(self, service):
        """Test setting coordinate captured callback."""
        callback = Mock()
        service.set_callback(callback)
        assert service.on_coord_captured == callback

    @pytest.mark.unit
    def test_on_click_success(self, service):
        """Test successful click handling."""
        with patch("coordinate_service.mouse.Button") as mock_button:
            mock_button.left = "left"
            service.capture_active = True
            service.capture_key = "input"

            with patch.object(service, "stop_capture") as mock_stop:
                with patch.object(service, "set_coordinate") as mock_set:
                    service._on_click(100, 200, "left", True)

                    mock_stop.assert_called_once()
                    mock_set.assert_called_once_with("input", (100, 200))

    @pytest.mark.unit
    def test_on_click_not_capturing(self, service):
        """Test click handling when not capturing."""
        with patch.object(service, "stop_capture") as mock_stop:
            service._on_click(100, 200, "left", True)
            mock_stop.assert_not_called()

    @pytest.mark.unit
    def test_on_click_not_pressed(self, service):
        """Test click handling when button not pressed."""
        service.capture_active = True
        with patch.object(service, "stop_capture") as mock_stop:
            service._on_click(100, 200, "left", False)
            mock_stop.assert_not_called()

    @pytest.mark.unit
    def test_on_click_wrong_button(self, service):
        """Test click handling with wrong button."""
        with patch("coordinate_service.mouse.Button") as mock_button:
            mock_button.left = "left"
            service.capture_active = True
            with patch.object(service, "stop_capture") as mock_stop:
                service._on_click(100, 200, "right", True)
                mock_stop.assert_not_called()

    @pytest.mark.unit
    def test_on_click_callback_error(self, service):
        """Test click handling with callback error."""
        with patch("coordinate_service.mouse.Button") as mock_button:
            mock_button.left = "left"
            service.capture_active = True
            service.capture_key = "input"
            callback = Mock(side_effect=Exception("Callback error"))
            service.on_coord_captured = callback

            with patch.object(service, "stop_capture") as mock_stop:
                service._on_click(100, 200, "left", True)
                # stop_capture is called once in the try block and once in the except block
                assert mock_stop.call_count >= 1

    @pytest.mark.unit
    def test_get_target_keys(self, service):
        """Test getting target keys."""
        keys = service.get_target_keys()
        assert keys == ["input", "submit", "accept"]
        assert keys is not service.get_target_keys()  # Should be a copy

    @pytest.mark.unit
    def test_get_target_label(self, service):
        """Test getting target label."""
        label = service.get_target_label("input")
        assert label == "Input"

    @pytest.mark.unit
    def test_get_target_label_invalid(self, service):
        """Test getting label for invalid target."""
        label = service.get_target_label("invalid")
        assert label == "Invalid"

    @pytest.mark.unit
    def test_validate_coordinates_success(self, service, sample_coordinates):
        """Test successful coordinate validation."""
        service.coords = sample_coordinates.copy()
        result = service.validate_coordinates()

        assert result["input"] is True
        assert result["submit"] is True
        assert result["accept"] is True

    @pytest.mark.unit
    def test_validate_coordinates_missing(self, service):
        """Test coordinate validation with missing coordinates."""
        service.coords = {"input": (100, 200)}  # Missing submit and accept

        result = service.validate_coordinates()

        assert result["input"] is True
        assert result["submit"] is False
        assert result["accept"] is False

    @pytest.mark.unit
    def test_validate_coordinates_invalid(self, service):
        """Test coordinate validation with invalid coordinates."""
        service.coords = {
            "input": (-1, 200),  # Invalid x coordinate
            "submit": (300, -1),  # Invalid y coordinate
            "accept": (500, 600),
        }

        result = service.validate_coordinates()

        assert result["input"] is False  # Invalid coordinate
        assert result["submit"] is False  # Invalid coordinate
        assert result["accept"] is True   # Valid coordinate

    @pytest.mark.unit
    def test_validate_coordinate_success(self, service):
        """Test successful single coordinate validation."""
        service.coords["input"] = (100, 200)
        result = service.validate_coordinate("input")
        assert result is True

    @pytest.mark.unit
    def test_validate_coordinate_invalid_x(self, service):
        """Test coordinate validation with invalid x coordinate."""
        service.coords["input"] = (-1, 200)
        result = service.validate_coordinate("input")
        assert result is False

    @pytest.mark.unit
    def test_validate_coordinate_invalid_y(self, service):
        """Test coordinate validation with invalid y coordinate."""
        service.coords["input"] = (100, -1)
        result = service.validate_coordinate("input")
        assert result is False

    @pytest.mark.unit
    def test_validate_coordinate_invalid_type(self, service):
        """Test coordinate validation with invalid type."""
        service.coords["input"] = "not a tuple"
        result = service.validate_coordinate("input")
        assert result is False

    @pytest.mark.unit
    def test_validate_coordinate_wrong_length(self, service):
        """Test coordinate validation with wrong tuple length."""
        service.coords["input"] = (100, 200, 300)
        result = service.validate_coordinate("input")
        assert result is False

    @pytest.mark.unit
    def test_save_coordinates_success(self, service):
        """Test successful coordinate saving."""
        with patch("coordinate_service.save_coords") as mock_save:
            service.coords = {"input": (100, 200)}
            service.save_coordinates()
            mock_save.assert_called_once_with({"input": (100, 200)})

    @pytest.mark.unit
    def test_save_coordinates_error(self, service):
        """Test coordinate saving with error."""
        with patch("coordinate_service.save_coords", side_effect=Exception("Save error")):
            service.coords = {"input": (100, 200)}
            service.save_coordinates()  # Should not raise error

    @pytest.mark.unit
    def test_load_coordinates_success(self, service):
        """Test successful coordinate loading."""
        with patch("coordinate_service.load_coords", return_value={"input": (100, 200)}):
            service._load_coordinates()
            assert service.coords == {"input": (100, 200)}

    @pytest.mark.unit
    def test_load_coordinates_error(self, service):
        """Test coordinate loading with error."""
        with patch("coordinate_service.load_coords", side_effect=Exception("Load error")):
            service._load_coordinates()
            assert service.coords == {}
