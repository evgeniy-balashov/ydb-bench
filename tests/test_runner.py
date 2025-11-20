"""Tests for runner.py module."""

import pytest

from ydb_bench.runner import split_range


class TestSplitRange:
    """Test cases for the split_range function."""

    def test_basic_split(self):
        """Test basic range splitting into equal parts."""
        result = split_range(1, 100, 4)
        expected = [(1, 25), (26, 50), (51, 75), (76, 100)]
        assert result == expected

    def test_single_range(self):
        """Test splitting into a single range (no split)."""
        result = split_range(1, 100, 1)
        expected = [(1, 100)]
        assert result == expected

    def test_more_splits_than_elements(self):
        """Test when count is greater than the range size."""
        result = split_range(1, 5, 10)
        # Should create 10 ranges with duplicates of single elements
        expected = [(1, 1), (1, 1), (2, 2), (2, 2), (3, 3), (3, 3), (4, 4), (4, 4), (5, 5), (5, 5)]
        assert len(result) == 10
        assert result == expected
        # Verify all ranges are non-empty
        for r in result:
            assert r[0] <= r[1]

    def test_exact_division(self):
        """Test when range divides evenly by count."""
        result = split_range(0, 99, 10)
        expected = [
            (0, 9),
            (10, 19),
            (20, 29),
            (30, 39),
            (40, 49),
            (50, 59),
            (60, 69),
            (70, 79),
            (80, 89),
            (90, 99),
        ]
        assert result == expected

    def test_uneven_division(self):
        """Test when range doesn't divide evenly."""
        result = split_range(1, 10, 3)
        # Total size = 10, split into 3: floor(10/3) = 3 per range
        # First two ranges get 3 elements, last gets remainder
        expected = [(1, 3), (4, 6), (7, 10)]
        assert result == expected

    def test_small_range(self):
        """Test with a very small range."""
        result = split_range(1, 2, 2)
        expected = [(1, 1), (2, 2)]
        assert result == expected

    def test_single_element_range(self):
        """Test with a range containing only one element."""
        result = split_range(5, 5, 1)
        expected = [(5, 5)]
        assert result == expected

    def test_single_element_multiple_splits(self):
        """Test splitting a single element into multiple ranges."""
        result = split_range(5, 5, 3)
        expected = [(5, 5), (5, 5), (5, 5)]
        assert len(result) == 3
        assert result == expected

    def test_large_range(self):
        """Test with a large range."""
        result = split_range(1, 1000000, 100)
        assert len(result) == 100
        assert result[0][0] == 1
        assert result[-1][1] == 1000000
        # Verify no gaps or overlaps
        for i in range(len(result) - 1):
            assert result[i][1] + 1 == result[i + 1][0]

    def test_negative_range(self):
        """Test with negative numbers."""
        result = split_range(-100, -1, 4)
        assert len(result) == 4
        assert result[0][0] == -100
        assert result[-1][1] == -1

    def test_range_crossing_zero(self):
        """Test with a range that crosses zero."""
        result = split_range(-50, 50, 2)
        expected = [(-50, -1), (0, 50)]
        assert result == expected

    def test_zero_count_raises_error(self):
        """Test that count=0 raises ValueError."""
        with pytest.raises(ValueError, match="count must be positive"):
            split_range(1, 100, 0)

    def test_negative_count_raises_error(self):
        """Test that negative count raises ValueError."""
        with pytest.raises(ValueError, match="count must be positive"):
            split_range(1, 100, -5)

    def test_start_greater_than_end_raises_error(self):
        """Test that start > end raises ValueError."""
        with pytest.raises(ValueError, match="start must be <= end"):
            split_range(100, 1, 4)

    def test_no_gaps_between_ranges(self):
        """Verify there are no gaps between consecutive ranges."""
        result = split_range(1, 100, 7)
        for i in range(len(result) - 1):
            # Next range should start immediately after current range ends
            assert result[i][1] + 1 == result[i + 1][0]

    def test_no_overlaps_between_ranges(self):
        """Verify there are no overlaps between ranges when count <= total_size."""
        result = split_range(1, 100, 5)
        for i in range(len(result) - 1):
            # Current range end should be less than next range start
            assert result[i][1] < result[i + 1][0]
        
        # When count > total_size, ranges can overlap (duplicates allowed)
        result_with_duplicates = split_range(1, 2, 3)
        # This should have duplicates: [(1, 1), (1, 1), (2, 2)]
        assert result_with_duplicates == [(1, 1), (1, 1), (2, 2)]

    def test_all_elements_covered(self):
        """Verify that all elements in the original range are covered."""
        start, end, count = 1, 100, 7
        result = split_range(start, end, count)
        
        # First range should start at start
        assert result[0][0] == start
        # Last range should end at end
        assert result[-1][1] == end
        
        # Calculate total elements covered
        total_covered = sum(r[1] - r[0] + 1 for r in result)
        expected_total = end - start + 1
        assert total_covered == expected_total

    def test_range_sizes_are_balanced(self):
        """Verify that range sizes are as balanced as possible."""
        result = split_range(1, 100, 4)
        sizes = [r[1] - r[0] + 1 for r in result]
        # All sizes should be equal (25) for this evenly divisible case
        assert all(size == 25 for size in sizes)

    def test_range_sizes_differ_by_at_most_one(self):
        """Verify that in uneven splits (when count <= total_size), sizes differ by at most 1."""
        result = split_range(1, 100, 7)
        sizes = [r[1] - r[0] + 1 for r in result]
        min_size = min(sizes)
        max_size = max(sizes)
        # Sizes should differ by at most 1
        assert max_size - min_size <= 1
        
        # When count > total_size, all ranges have size 1
        result_single = split_range(1, 5, 10)
        sizes_single = [r[1] - r[0] + 1 for r in result_single]
        assert all(size == 1 for size in sizes_single)

    def test_pgbench_typical_case(self):
        """Test a typical pgbench scenario with branch IDs."""
        # Typical case: 100 branches split among 10 workers
        result = split_range(1, 100, 10)
        assert len(result) == 10
        # Each worker should get 10 branches
        for r in result:
            assert r[1] - r[0] + 1 == 10

    def test_return_type(self):
        """Verify the return type is a list of tuples."""
        result = split_range(1, 10, 3)
        assert isinstance(result, list)
        assert all(isinstance(r, tuple) for r in result)
        assert all(len(r) == 2 for r in result)
        assert all(isinstance(r[0], int) and isinstance(r[1], int) for r in result)

    def test_count_exceeds_range_creates_duplicates(self):
        """Test that when count > range size, duplicates are created correctly."""
        result = split_range(1, 2, 3)
        expected = [(1, 1), (1, 1), (2, 2)]
        assert result == expected
        assert len(result) == 3
        
        result2 = split_range(1, 3, 5)
        assert len(result2) == 5
        # All ranges should be single elements
        assert all(r[0] == r[1] for r in result2)
        
    def test_all_ranges_non_empty(self):
        """Verify that all ranges are non-empty (start <= end)."""
        # Test various cases
        test_cases = [
            (1, 100, 4),
            (1, 5, 10),
            (1, 2, 3),
            (5, 5, 3),
            (1, 10, 1),
            (-10, 10, 7),
        ]
        for start, end, count in test_cases:
            result = split_range(start, end, count)
            for r in result:
                assert r[0] <= r[1], f"Invalid range {r} in split_range({start}, {end}, {count})"