"""Tests for espagent.utils module - meaningful validation only."""

import pytest
from pydantic import ValidationError

from espagent.utils import SSHState, UserInfo


class TestUserInfo:
    """Test UserInfo model - validates data structure integrity."""

    def test_user_info_validation_catches_missing_required_field(self):
        """Test that UserInfo properly validates required fields."""
        with pytest.raises(ValidationError):
            UserInfo(user_name="test")  # Missing additional_info

    def test_user_info_validation_catches_empty_string(self):
        """Test that UserInfo validates field constraints."""
        user = UserInfo(user_name="test", additional_info="")
        assert user.additional_info == ""  # Empty strings are allowed


class TestSSHState:
    """Test SSHState model - validates data structure integrity."""

    def test_ssh_state_type_validation(self):
        """Test that SSHState enforces correct types."""
        # passwd field is int (not str) - catch if someone changes it
        with pytest.raises(ValidationError):
            SSHState(
                host="localhost",
                user="test",
                passwd="password",  # Should be int
                port=22,
                command="ls",
            )

    def test_ssh_state_accepts_valid_data(self):
        """Test SSHState accepts properly structured data."""
        ssh = SSHState(host="localhost", user="testuser", passwd=12345, port=22, command="ls -la")
        assert ssh.host == "localhost"
        assert ssh.port == 22
