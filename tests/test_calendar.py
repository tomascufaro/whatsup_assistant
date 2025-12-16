"""
Tests for calendar tool functionality.
"""

import pytest
from src.tools.calendar import CalendarTool


def test_calendar_tool_initialization():
    """Test that calendar tool can be initialized."""
    # Note: This will require Google OAuth setup
    # For now, we'll just test the structure
    tool = CalendarTool()
    assert tool.name == "google_calendar"
    assert "calendar" in tool.description.lower()


def test_calendar_input_schema():
    """Test calendar input schema validation."""
    from src.tools.calendar import CalendarInput
    
    input_data = CalendarInput(
        action="list"
    )
    assert input_data.action == "list"


if __name__ == "__main__":
    pytest.main([__file__])

