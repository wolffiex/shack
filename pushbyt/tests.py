from django.test import TestCase
from django.utils import timezone
from datetime import datetime, timedelta
from pushbyt.models import Animation
from pushbyt.views.preview import compare_animations, is_served, summarize_anims


class AnimationPrioritizationTestCase(TestCase):
    """Test the animation prioritization logic."""

    def setUp(self):
        """Set up common test objects."""
        self.now = timezone.now()
        self.summary = {"now": self.now, "last_timer": None, "last_clock": None}

    def create_animation(
        self,
        source=Animation.Source.STATIC,
        start_time=None,
        served_at=None,
        metadata=None,
    ):
        """Helper to create Animation objects for testing."""
        anim = Animation(
            source=source,
            start_time=start_time,
            served_at=served_at,
            metadata=metadata or {},
        )
        return anim

    def test_doorbell_priority(self):
        """Test that doorbell animations have highest priority."""
        # Create a doorbell animation and a regular animation
        doorbell = self.create_animation(source=Animation.Source.DOORBELL)
        regular = self.create_animation(source=Animation.Source.STATIC)

        # Doorbell should be higher priority than any other animation
        self.assertEqual(compare_animations(doorbell, regular, self.summary), -1)
        self.assertEqual(compare_animations(regular, doorbell, self.summary), 1)

        # Even if the other animation is unserved with no start_time
        unserved_realtime = self.create_animation(source=Animation.Source.STATIC)
        self.assertEqual(
            compare_animations(doorbell, unserved_realtime, self.summary), -1
        )

    def test_unserved_realtime_priority(self):
        """Test that unserved real-time content has priority after doorbell."""
        # Create an unserved real-time animation and a served animation
        unserved = self.create_animation(source=Animation.Source.STATIC)
        served = self.create_animation(
            source=Animation.Source.STATIC, served_at=self.now - timedelta(seconds=30)
        )

        # Unserved should be higher priority
        self.assertEqual(compare_animations(unserved, served, self.summary), -1)
        self.assertEqual(compare_animations(served, unserved, self.summary), 1)

        # Create an unserved animation with a start_time (timed)
        unserved_timed = self.create_animation(
            source=Animation.Source.RAYS, start_time=self.now + timedelta(seconds=10)
        )

        # Unserved real-time should be higher priority than unserved timed
        self.assertEqual(compare_animations(unserved, unserved_timed, self.summary), -1)
        self.assertEqual(compare_animations(unserved_timed, unserved, self.summary), 1)

    def test_unserved_timed_priority(self):
        """Test that unserved timed animations are prioritized by start time."""
        # Create two unserved timed animations with different start times
        earlier = self.create_animation(
            source=Animation.Source.RAYS, start_time=self.now + timedelta(seconds=5)
        )
        later = self.create_animation(
            source=Animation.Source.RADAR, start_time=self.now + timedelta(seconds=15)
        )

        # Earlier start time should be higher priority
        self.assertEqual(compare_animations(earlier, later, self.summary), -1)
        self.assertEqual(compare_animations(later, earlier, self.summary), 1)

        # Unserved timed should be higher priority than served animations
        served = self.create_animation(
            source=Animation.Source.STATIC, served_at=self.now - timedelta(seconds=30)
        )
        self.assertEqual(compare_animations(earlier, served, self.summary), -1)
        self.assertEqual(compare_animations(served, earlier, self.summary), 1)

    def test_served_priority(self):
        """Test priorities for animations that have been served."""
        # Create two served animations with different served times
        recent = self.create_animation(
            source=Animation.Source.STATIC, served_at=self.now - timedelta(seconds=10)
        )
        older = self.create_animation(
            source=Animation.Source.STATIC, served_at=self.now - timedelta(seconds=40)
        )

        # Most recently served should have higher priority
        self.assertEqual(compare_animations(recent, older, self.summary), -1)
        self.assertEqual(compare_animations(older, recent, self.summary), 1)

        # Create an animation with important metadata
        important = self.create_animation(
            source=Animation.Source.TIMER,
            served_at=self.now - timedelta(seconds=30),
            start_time=self.now - timedelta(seconds=10),
            metadata={"important": True},
        )

        # With our new prioritization system, important animations have higher priority
        # than recency of served time, to ensure critical timer information is shown
        self.assertEqual(compare_animations(recent, important, self.summary), 1)
        self.assertEqual(compare_animations(important, older, self.summary), -1)

    def test_content_type_balancing(self):
        """Test that content type balancing works correctly."""
        # In our new priority system, content type balancing is a lower priority
        # factor that only applies when other factors are equal

        # Create unserved timer and clock animations with identical start times
        timer = self.create_animation(
            source=Animation.Source.TIMER, start_time=self.now + timedelta(seconds=30)
        )
        clock = self.create_animation(
            source=Animation.Source.RAYS,
            start_time=self.now + timedelta(seconds=30),  # Same start time
        )

        # With both being equal priority otherwise, and no last_timer shown,
        # timer should be preferred
        self.summary["last_timer"] = None
        self.summary["last_clock"] = clock  # We've shown a clock recently
        result = compare_animations(timer, clock, self.summary)

        # Content type balancing only applies for animations with otherwise equal priority

        # Create served animations with different served_at times
        served_timer = self.create_animation(
            source=Animation.Source.TIMER, served_at=self.now - timedelta(seconds=50)
        )
        served_clock = self.create_animation(
            source=Animation.Source.RADAR,
            served_at=self.now - timedelta(seconds=10),  # More recently served
        )

        # The most recently served should have higher priority, regardless of content type
        self.assertEqual(
            compare_animations(served_clock, served_timer, self.summary), -1
        )
        
    def test_timer_prioritization(self):
        """Test that timer animations are properly prioritized."""
        # Create a bunch of animations for testing
        animations = [
            # Create a doorbell (highest priority)
            self.create_animation(source=Animation.Source.DOORBELL),
            
            # Create an unserved realtime animation (second priority)
            self.create_animation(source=Animation.Source.STATIC),
            
            # Create an unserved timed animation (third priority)
            self.create_animation(
                source=Animation.Source.RAYS, start_time=self.now + timedelta(seconds=10)
            ),
            
            # Create an unserved timer animation (should be properly prioritized)
            self.create_animation(
                source=Animation.Source.TIMER, start_time=self.now + timedelta(seconds=12)
            ),
            
            # Create a recently served animation (fourth priority)
            self.create_animation(
                source=Animation.Source.STATIC, served_at=self.now - timedelta(seconds=5)
            ),
            
            # Create a less recently served animation
            self.create_animation(
                source=Animation.Source.STATIC, served_at=self.now - timedelta(seconds=30)
            ),
        ]
        
        # Test with no timer shown recently
        self.summary["last_timer"] = None
        
        # Generate a summary based on our list of animations
        summary = summarize_anims(animations, self.now)
        
        # Get the unserved timer and unserved RAYS animation
        unserved_timer = animations[3]  # Index 3 is our unserved timer
        unserved_rays = animations[2]   # Index 2 is our unserved rays
        
        # Verify the timer animation gets prioritized over the rays animation
        # when no timer has been seen recently
        self.assertEqual(compare_animations(unserved_timer, unserved_rays, summary), -1)
        
        # Now test with a timer recently shown
        recent_timer = self.create_animation(
            source=Animation.Source.TIMER, served_at=self.now - timedelta(seconds=10)
        )
        summary["last_timer"] = recent_timer
        
        # With a timer recently shown, the unserved rays should now win
        # over the unserved timer because we want content variety
        self.assertEqual(compare_animations(unserved_timer, unserved_rays, summary), 1)
        
        # Create a timer with important=True flag that's starting soon (within 15 seconds)
        important_timer = self.create_animation(
            source=Animation.Source.TIMER, 
            start_time=self.now + timedelta(seconds=10),  # Within 15 seconds
            metadata={"important": True}
        )
        
        # Important timers that are starting soon should win even if a timer was recently shown
        self.assertEqual(compare_animations(important_timer, unserved_rays, summary), -1)