from django.test import TestCase
from django.utils import timezone
from datetime import datetime, timedelta
from pushbyt.models import Animation
from pushbyt.animation.generate import get_segment_start, SEGMENT_TIME
import logging

# Disable logging during tests
logging.disable(logging.CRITICAL)


class GenerationTestCase(TestCase):
    """Tests for the animation generation logic."""

    def setUp(self):
        """Set up common test objects."""
        self.now = timezone.now()
        self.aligned_time = Animation.align_time(self.now)

        # Create test animation sources
        self.ray_source = Animation.Source.RAYS
        self.radar_source = Animation.Source.RADAR
        self.sources = [self.ray_source, self.radar_source]

    def create_animation(self, source=Animation.Source.RAYS, start_time=None):
        """Helper to create Animation objects for testing."""
        anim = Animation(
            source=source, start_time=start_time, file_path="test_path.webp"
        )
        anim.save()
        return anim

    def test_get_segment_start_no_animations(self):
        """Test get_segment_start when there are no existing animations."""
        # When there are no animations, it should return the aligned start time
        start_time = get_segment_start(self.aligned_time, *self.sources)
        self.assertEqual(start_time, self.aligned_time)

    def test_get_segment_start_with_future_coverage(self):
        """Test get_segment_start when we have sufficient future coverage."""
        # Create animations that extend beyond SEGMENT_TIME into the future
        for i in range(10):
            future_time = self.aligned_time + timedelta(seconds=i * 10)
            self.create_animation(start_time=future_time)

        # The furthest animation is now aligned_time + 90 seconds
        # This should be enough coverage, so get_segment_start should return None
        start_time = get_segment_start(self.aligned_time, *self.sources)
        self.assertIsNone(start_time)

    def test_get_segment_start_with_partial_coverage(self):
        """Test get_segment_start when we have insufficient future coverage."""
        # Create animations that extend only 30 seconds into the future
        max_future = self.aligned_time + timedelta(seconds=30)
        for i in range(4):
            future_time = self.aligned_time + timedelta(seconds=i * 10)
            self.create_animation(start_time=future_time)

        # We have animations up to aligned_time + 30s, but SEGMENT_TIME is 90s
        # So we need more animations starting after our last animation
        start_time = get_segment_start(self.aligned_time, *self.sources)

        # Check that the returned time is after our max_future time
        self.assertIsNotNone(start_time)
        self.assertTrue(start_time > max_future)

        # Verify it's aligned to a valid time slot (seconds should be 0, 10, 20, 30, 40, or 50)
        self.assertIn(start_time.second, [0, 10, 20, 30, 40, 50])

    def test_get_segment_start_ignores_past_animations(self):
        """Test that get_segment_start ignores animations from before start_time."""
        # Create an animation in the past
        past_time = self.aligned_time - timedelta(seconds=60)
        self.create_animation(start_time=past_time)

        # Since there are no animations >= aligned_time, we should get aligned_time
        start_time = get_segment_start(self.aligned_time, *self.sources)
        self.assertEqual(start_time, self.aligned_time)

    def test_get_segment_start_respects_sources(self):
        """Test that get_segment_start only considers the specified sources."""
        # Create animations of a different source type
        for i in range(10):
            future_time = self.aligned_time + timedelta(seconds=i * 10)
            self.create_animation(source=Animation.Source.TIMER, start_time=future_time)

        # When filtering for RAYS/RADAR, it should ignore TIMER animations
        # So it should return the aligned time as if no animations exist
        start_time = get_segment_start(self.aligned_time, *self.sources)
        self.assertEqual(start_time, self.aligned_time)

    def test_get_segment_start_next_time_calculation(self):
        """Test that get_segment_start properly calculates the next start time."""
        # Create animations up to a certain point
        max_future = self.aligned_time + timedelta(seconds=40)
        self.create_animation(start_time=max_future)

        # We need more animations after max_future
        start_time = get_segment_start(self.aligned_time, *self.sources)

        # The start time should be after max_future
        self.assertIsNotNone(start_time)
        self.assertTrue(start_time > max_future)

        # The returned time should be properly aligned (seconds should be 0, 10, 20, 30, 40, or 50)
        self.assertIn(start_time.second, [0, 10, 20, 30, 40, 50])
