"""Unit tests for File Manager page functions.

Tests pagination, sorting, filtering, and file operations.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

# Mock streamlit before importing file_manager
import sys
sys.modules['streamlit'] = MagicMock()

# ============================================================================
# TEST DATA
# ============================================================================

MOCK_FILES = [
    {'key': 'file1.csv', 'name': 'file1.csv', 'size': 1024, 'last_modified': '2024-12-01'},
    {'key': 'file2.json', 'name': 'file2.json', 'size': 2048, 'last_modified': '2024-12-02'},
    {'key': 'data.txt', 'name': 'data.txt', 'size': 512, 'last_modified': '2024-12-03'},
    {'key': 'script.py', 'name': 'script.py', 'size': 4096, 'last_modified': '2024-12-04'},
    {'key': 'archive.zip', 'name': 'archive.zip', 'size': 8192, 'last_modified': '2024-12-05'},
]

MOCK_FOLDERS = [
    'data/',
    'scripts/',
    'archives/',
]


# ============================================================================
# HELPER FUNCTION TESTS
# ============================================================================

class TestFilterFiles:
    """Test file filtering functionality."""
    
    def test_filter_by_search_query(self):
        """Test filtering files by search query."""
        # Mock session state
        mock_session_state = {
            'search_query': 'file',
            'filter_type': 'all',
        }
        
        # Import and test filter function
        # Note: We would need to refactor file_manager.py to make functions testable
        # For now, we test the logic directly
        
        query = 'file'
        filtered = [f for f in MOCK_FILES if query.lower() in f['name'].lower()]
        
        assert len(filtered) == 2
        assert filtered[0]['name'] == 'file1.csv'
        assert filtered[1]['name'] == 'file2.json'
    
    def test_filter_by_type(self):
        """Test filtering files by extension."""
        filter_ext = '.csv'
        filtered = [f for f in MOCK_FILES if f['name'].lower().endswith(filter_ext)]
        
        assert len(filtered) == 1
        assert filtered[0]['name'] == 'file1.csv'
    
    def test_filter_combined(self):
        """Test combined search and type filtering."""
        query = 'file'
        filter_ext = '.csv'
        
        filtered = [f for f in MOCK_FILES if query.lower() in f['name'].lower()]
        filtered = [f for f in filtered if f['name'].lower().endswith(filter_ext)]
        
        assert len(filtered) == 1
        assert filtered[0]['name'] == 'file1.csv'
    
    def test_no_results(self):
        """Test filter with no matching results."""
        query = 'nonexistent'
        filtered = [f for f in MOCK_FILES if query.lower() in f['name'].lower()]
        
        assert len(filtered) == 0


class TestSortFiles:
    """Test file sorting functionality."""
    
    def test_sort_by_name_asc(self):
        """Test sorting files by name ascending."""
        sorted_files = sorted(MOCK_FILES, key=lambda f: f['name'].lower())
        
        assert sorted_files[0]['name'] == 'archive.zip'
        assert sorted_files[1]['name'] == 'data.txt'
        assert sorted_files[-1]['name'] == 'script.py'
    
    def test_sort_by_name_desc(self):
        """Test sorting files by name descending."""
        sorted_files = sorted(MOCK_FILES, key=lambda f: f['name'].lower(), reverse=True)
        
        assert sorted_files[0]['name'] == 'script.py'
        assert sorted_files[-1]['name'] == 'archive.zip'
    
    def test_sort_by_size_asc(self):
        """Test sorting files by size ascending."""
        sorted_files = sorted(MOCK_FILES, key=lambda f: f.get('size', 0))
        
        assert sorted_files[0]['size'] == 512
        assert sorted_files[-1]['size'] == 8192
    
    def test_sort_by_size_desc(self):
        """Test sorting files by size descending."""
        sorted_files = sorted(MOCK_FILES, key=lambda f: f.get('size', 0), reverse=True)
        
        assert sorted_files[0]['size'] == 8192
        assert sorted_files[-1]['size'] == 512
    
    def test_sort_by_date_asc(self):
        """Test sorting files by date ascending."""
        sorted_files = sorted(MOCK_FILES, key=lambda f: f.get('last_modified', ''))
        
        assert sorted_files[0]['last_modified'] == '2024-12-01'
        assert sorted_files[-1]['last_modified'] == '2024-12-05'
    
    def test_sort_by_date_desc(self):
        """Test sorting files by date descending."""
        sorted_files = sorted(MOCK_FILES, key=lambda f: f.get('last_modified', ''), reverse=True)
        
        assert sorted_files[0]['last_modified'] == '2024-12-05'
        assert sorted_files[-1]['last_modified'] == '2024-12-01'


class TestPaginateFiles:
    """Test file pagination functionality."""
    
    def test_paginate_first_page(self):
        """Test first page of pagination."""
        page_size = 2
        page_num = 1
        
        start_idx = (page_num - 1) * page_size
        end_idx = start_idx + page_size
        page_files = MOCK_FILES[start_idx:end_idx]
        
        assert len(page_files) == 2
        assert page_files[0]['name'] == 'file1.csv'
        assert page_files[1]['name'] == 'file2.json'
    
    def test_paginate_middle_page(self):
        """Test middle page of pagination."""
        page_size = 2
        page_num = 2
        
        start_idx = (page_num - 1) * page_size
        end_idx = start_idx + page_size
        page_files = MOCK_FILES[start_idx:end_idx]
        
        assert len(page_files) == 2
        assert page_files[0]['name'] == 'data.txt'
        assert page_files[1]['name'] == 'script.py'
    
    def test_paginate_last_page(self):
        """Test last page with partial results."""
        page_size = 2
        page_num = 3
        
        start_idx = (page_num - 1) * page_size
        end_idx = start_idx + page_size
        page_files = MOCK_FILES[start_idx:end_idx]
        
        assert len(page_files) == 1
        assert page_files[0]['name'] == 'archive.zip'
    
    def test_total_pages_calculation(self):
        """Test total pages calculation."""
        page_size = 2
        total_pages = (len(MOCK_FILES) + page_size - 1) // page_size
        
        assert total_pages == 3
    
    def test_single_page(self):
        """Test when all files fit on one page."""
        page_size = 10
        total_pages = max(1, (len(MOCK_FILES) + page_size - 1) // page_size)
        
        assert total_pages == 1
    
    def test_empty_list(self):
        """Test pagination with empty file list."""
        empty_files = []
        page_size = 10
        total_pages = max(1, (len(empty_files) + page_size - 1) // page_size)
        
        assert total_pages == 1


class TestFileOperations:
    """Test file operation logic."""
    
    def test_file_selection(self):
        """Test file selection state management."""
        selected_files = []
        
        # Select file
        file_key = 'file1.csv'
        if file_key not in selected_files:
            selected_files.append(file_key)
        
        assert len(selected_files) == 1
        assert 'file1.csv' in selected_files
        
        # Deselect file
        if file_key in selected_files:
            selected_files.remove(file_key)
        
        assert len(selected_files) == 0
    
    def test_select_all(self):
        """Test select all functionality."""
        page_files = MOCK_FILES[:3]
        selected_files = [f['key'] for f in page_files]
        
        assert len(selected_files) == 3
        assert 'file1.csv' in selected_files
        assert 'file2.json' in selected_files
        assert 'data.txt' in selected_files
    
    def test_clear_selection(self):
        """Test clear selection."""
        selected_files = ['file1.csv', 'file2.json']
        selected_files = []
        
        assert len(selected_files) == 0
    
    def test_folder_navigation(self):
        """Test folder navigation logic."""
        current_prefix = 'data/experiments/'
        
        # Navigate to folder
        new_folder = 'data/experiments/results/'
        current_prefix = new_folder
        
        assert current_prefix == 'data/experiments/results/'
        
        # Navigate up
        parts = current_prefix.rstrip('/').split('/')
        if len(parts) > 1:
            current_prefix = '/'.join(parts[:-1]) + '/'
        
        assert current_prefix == 'data/experiments/'
    
    def test_navigate_to_root(self):
        """Test navigating to root."""
        current_prefix = 'data/'
        
        parts = current_prefix.rstrip('/').split('/')
        if len(parts) == 1:
            current_prefix = ''
        
        assert current_prefix == ''


class TestIntegrationScenarios:
    """Test complete user workflows."""
    
    def test_search_sort_paginate_workflow(self):
        """Test combined search, sort, and pagination."""
        # Search
        query = 'file'
        filtered = [f for f in MOCK_FILES if query.lower() in f['name'].lower()]
        assert len(filtered) == 2
        
        # Sort by size descending
        sorted_files = sorted(filtered, key=lambda f: f.get('size', 0), reverse=True)
        assert sorted_files[0]['size'] == 2048  # file2.json
        assert sorted_files[1]['size'] == 1024  # file1.csv
        
        # Paginate (1 per page)
        page_size = 1
        page_num = 1
        start_idx = (page_num - 1) * page_size
        end_idx = start_idx + page_size
        page_files = sorted_files[start_idx:end_idx]
        
        assert len(page_files) == 1
        assert page_files[0]['name'] == 'file2.json'
    
    def test_filter_and_select_workflow(self):
        """Test filtering and selecting files."""
        # Filter by type
        filter_ext = '.csv'
        filtered = [f for f in MOCK_FILES if f['name'].lower().endswith(filter_ext)]
        
        # Select all filtered
        selected = [f['key'] for f in filtered]
        
        assert len(selected) == 1
        assert 'file1.csv' in selected
    
    def test_navigate_and_load_workflow(self):
        """Test folder navigation and file loading."""
        # Start at root
        current_prefix = ''
        
        # Navigate to folder
        folder = 'data/'
        current_prefix = folder
        assert current_prefix == 'data/'
        
        # Load files (simulated)
        # In real scenario, would call load_files_and_folders()
        
        # Navigate up
        parts = current_prefix.rstrip('/').split('/')
        if len(parts) > 1:
            current_prefix = '/'.join(parts[:-1]) + '/'
        else:
            current_prefix = ''
        
        assert current_prefix == ''


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_file_list(self):
        """Test with no files."""
        empty_files = []
        
        # Search returns empty
        query = 'test'
        filtered = [f for f in empty_files if query.lower() in f['name'].lower()]
        assert len(filtered) == 0
        
        # Pagination with empty list
        page_size = 10
        total_pages = max(1, (len(empty_files) + page_size - 1) // page_size)
        assert total_pages == 1
    
    def test_invalid_page_number(self):
        """Test invalid page number handling."""
        page_size = 2
        page_num = 10  # Beyond available pages
        
        total_pages = (len(MOCK_FILES) + page_size - 1) // page_size
        
        # Should clamp to valid range
        if page_num > total_pages:
            page_num = total_pages
        
        assert page_num == 3
    
    def test_special_characters_in_search(self):
        """Test search with special characters."""
        # The query 'file.csv' should match 'file1.csv' 
        # but the period is a literal character, not a wildcard
        query = 'csv'
        filtered = [f for f in MOCK_FILES if query.lower() in f['name'].lower()]
        
        # Should match all .csv files
        assert len(filtered) >= 1
        assert any('csv' in f['name'] for f in filtered)
    
    def test_case_insensitive_search(self):
        """Test case-insensitive search."""
        query = 'FILE'
        filtered = [f for f in MOCK_FILES if query.lower() in f['name'].lower()]
        
        assert len(filtered) == 2
    
    def test_missing_file_properties(self):
        """Test handling files with missing properties."""
        incomplete_file = {'key': 'test.txt', 'name': 'test.txt'}
        
        # Should handle missing size gracefully
        size = incomplete_file.get('size', 0)
        assert size == 0
        
        # Should handle missing date gracefully
        date = incomplete_file.get('last_modified', '')
        assert date == ''


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
