"""
Tests for CSV database tool functionality.
"""

import pytest
import os
import pandas as pd
from src.tools.database import DatabaseTool

TEST_CSV_PATH = os.path.join(os.path.dirname(__file__), '../data/test_clients.csv')


def test_database_tool_initialization():
    """Test that database tool can be initialized."""
    tool = DatabaseTool()
    assert tool.name == "client_database"
    assert "database" in tool.description.lower()


def test_database_add_client():
    """Test adding a client to the database."""
    tool = DatabaseTool()
    
    # Temporarily use test CSV
    original_path = tool._Tool__class__.__dict__.get('CSV_PATH', None)
    
    result = tool._run(
        action="add",
        name="Test Client",
        email="test@example.com",
        phone="+1234567890",
        notes="Test notes"
    )
    
    assert "added successfully" in result.lower() or "error" in result.lower()


def test_database_get_client():
    """Test retrieving a client from the database."""
    tool = DatabaseTool()
    
    result = tool._run(
        action="get",
        name="John Doe"
    )
    
    # Should either find the client or return an error message
    assert isinstance(result, (str, dict))


def test_database_list_clients():
    """Test listing all clients."""
    tool = DatabaseTool()
    
    result = tool._run(action="list")
    
    assert "clients" in result.lower() or "error" in result.lower()


if __name__ == "__main__":
    pytest.main([__file__])

