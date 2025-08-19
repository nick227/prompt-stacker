#!/usr/bin/env python3
"""
Virtual Automation Emulator - Comprehensive Testing Tool

This tool provides a virtual environment for testing automation scenarios
without requiring real UI interactions. It emulates all the key components
and allows for controlled testing of pause/resume, automation flow, and
edge cases.
"""

import time
import threading
import logging
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass
from enum import Enum
import queue

# Configure logging for testing
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# =============================================================================
# VIRTUAL COMPONENTS
# =============================================================================

class AutomationState(Enum):
    """Automation state enumeration."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"

@dataclass
class VirtualCoordinates:
    """Virtual coordinate system."""
    input: Tuple[int, int] = (100, 100)
    submit: Tuple[int, int] = (200, 100)
    accept: Tuple[int, int] = (300, 100)

@dataclass
class VirtualTimers:
    """Virtual timer configuration."""
    start_delay: float = 2.0
    main_wait: float = 5.0
    cooldown: float = 1.0
    get_ready_delay: float = 2.0

class VirtualCountdownService:
    """Virtual countdown service for testing."""
    
    def __init__(self):
        self._active = False
        self._paused = False
        self._cancelled = False
        self._thread = None
        self._lock = threading.Lock()
        self._completion_event = threading.Event()
        self._stop_event = threading.Event()
        self._current_remaining = 0.0
        self._current_total = 0.0
        self._display_updates = []
        self._state_changes = []
        
    def start_countdown(self, seconds: float, text: str = None, next_text: str = None, last_text: str = None) -> Dict[str, Any]:
        """Start a virtual countdown."""
        logger.info(f"Virtual countdown started: {seconds}s")
        
        # Stop any existing countdown
        self.stop()
        
        # Reset state
        with self._lock:
            self._active = True
            self._paused = False
            self._cancelled = False
            self._current_total = seconds
            self._current_remaining = seconds
            
        # Clear events
        self._stop_event.clear()
        self._completion_event.clear()
        
        # Start countdown thread
        self._thread = threading.Thread(target=self._countdown_loop, daemon=True)
        self._thread.start()
        
        # Don't wait for completion - let it run independently
        # The calling code should handle the result when needed
        
        return {"started": True}
        
    def _countdown_loop(self):
        """Virtual countdown loop."""
        try:
            while (self._current_remaining > 0 and 
                   self._active and 
                   not self._cancelled and 
                   not self._stop_event.is_set()):
                
                # Handle pause state
                if self._paused:
                    self._record_state_change("PAUSED", self._current_remaining)
                    time.sleep(0.1)  # Virtual tick
                    continue
                
                # Update display
                self._record_display_update(self._current_remaining, self._current_total)
                
                # Wait for next tick
                time.sleep(1.0)
                
                # Decrement remaining time ONLY when not paused
                self._current_remaining -= 1.0
                
            # Countdown completed
            with self._lock:
                self._active = False
                
            # Signal completion
            self._completion_event.set()
            
        except Exception as e:
            logger.error(f"Error in virtual countdown loop: {e}")
            self._completion_event.set()
    
    def toggle_pause(self):
        """Toggle pause state."""
        if not self._active:
            logger.warning("Cannot toggle pause - countdown not active")
            return
            
        with self._lock:
            self._paused = not self._paused
            state = "PAUSED" if self._paused else "RESUMED"
            self._record_state_change(state, self._current_remaining)
            
        logger.info(f"Virtual countdown {state.lower()}")
    
    def stop(self):
        """Stop the countdown."""
        with self._lock:
            self._active = False
            self._cancelled = True
            
        self._stop_event.set()
        self._completion_event.set()
        
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
            self._thread = None
    
    def is_active(self) -> bool:
        """Check if countdown is active."""
        return self._active
    
    def is_paused(self) -> bool:
        """Check if countdown is paused."""
        return self._paused
    
    def is_cancelled(self) -> bool:
        """Check if countdown is cancelled."""
        return self._cancelled
    
    def force_reset(self):
        """Force reset the countdown service."""
        self.stop()
        with self._lock:
            self._active = False
            self._paused = False
            self._cancelled = False
            self._current_remaining = 0.0
            self._current_total = 0.0
    
    def _get_final_state(self) -> Dict[str, Any]:
        """Get final state."""
        with self._lock:
            return {
                "cancelled": self._cancelled,
                "paused": self._paused,
            }
    
    def _record_display_update(self, remaining: float, total: float):
        """Record display update for testing."""
        self._display_updates.append({
            "timestamp": time.time(),
            "remaining": remaining,
            "total": total,
            "paused": self._paused
        })
    
    def _record_state_change(self, state: str, remaining: float):
        """Record state change for testing."""
        self._state_changes.append({
            "timestamp": time.time(),
            "state": state,
            "remaining": remaining
        })
    
    def get_test_data(self) -> Dict[str, Any]:
        """Get test data for analysis."""
        return {
            "display_updates": self._display_updates,
            "state_changes": self._state_changes,
            "final_remaining": self._current_remaining,
            "final_total": self._current_total
        }

class VirtualUI:
    """Virtual UI for testing automation."""
    
    def __init__(self, prompts: List[str], coordinates: VirtualCoordinates, timers: VirtualTimers):
        self.prompts = prompts
        self.coordinates = coordinates
        self.timers = timers
        self.current_prompt_index = 0
        self.countdown_service = VirtualCountdownService()
        self.automation_state = AutomationState.IDLE
        self.automation_events = []
        self._automation_lock = threading.Lock()
        
    def get_prompts_safe(self) -> List[str]:
        """Get prompts safely."""
        return self.prompts.copy()
    
    def get_coords(self) -> Dict[str, Tuple[int, int]]:
        """Get coordinates."""
        return {
            "input": self.coordinates.input,
            "submit": self.coordinates.submit,
            "accept": self.coordinates.accept
        }
    
    def get_timers(self) -> Tuple[float, float, float, float]:
        """Get timers."""
        return (
            self.timers.start_delay,
            self.timers.main_wait,
            self.timers.cooldown,
            self.timers.get_ready_delay
        )
    
    def countdown(self, seconds: float, text: str = None, next_text: str = None, last_text: str = None) -> Dict[str, Any]:
        """Start countdown."""
        self._record_automation_event("COUNTDOWN_START", {"seconds": seconds, "text": text})
        return self.countdown_service.start_countdown(seconds, text, next_text, last_text)
    
    def update_prompt_index_from_automation(self, index: int):
        """Update prompt index."""
        self.current_prompt_index = index
        self._record_automation_event("PROMPT_INDEX_UPDATE", {"index": index})
    
    def _record_automation_event(self, event_type: str, data: Dict[str, Any]):
        """Record automation event for testing."""
        self.automation_events.append({
            "timestamp": time.time(),
            "event": event_type,
            "data": data
        })

class VirtualSessionController:
    """Virtual session controller for testing."""
    
    def __init__(self, ui: VirtualUI):
        self.ui = ui
        self._started = False
        self._automation_lock = threading.Lock()
        self._prompts_locked = False
        self.controller_events = []
        
    def start_automation(self) -> bool:
        """Start automation."""
        with self._automation_lock:
            if self._started:
                logger.warning("Automation already started")
                return False
            
            # Reset countdown
            self.ui.countdown_service.force_reset()
            
            # Validate prerequisites
            if not self._validate_start_prerequisites():
                return False
                
            self._prompts_locked = True
            self._started = True
            self._record_controller_event("AUTOMATION_STARTED")
            
            # Start automation thread
            self._start_automation_thread()
            return True
    
    def stop_automation(self):
        """Stop automation."""
        with self._automation_lock:
            self._reset_automation_state()
            self._stop_countdown_if_active()
            self._record_controller_event("AUTOMATION_STOPPED")
    
    def next_prompt(self):
        """Advance to next prompt."""
        with self._automation_lock:
            if not self._started:
                # Just advance UI position
                if self.ui.current_prompt_index < len(self.ui.prompts) - 1:
                    self.ui.current_prompt_index += 1
                    self._record_controller_event("PROMPT_ADVANCED", {"index": self.ui.current_prompt_index})
                return
            
            # If automation is running, advance and potentially start new cycle
            if self.ui.current_prompt_index < len(self.ui.prompts) - 1:
                self._stop_countdown_if_active()
                
                self.ui.current_prompt_index += 1
                self._record_controller_event("PROMPT_ADVANCED", {"index": self.ui.current_prompt_index})
                
                # CRITICAL FIX: Only start automation cycle if NOT paused
                if not self.ui.countdown_service.is_paused():
                    self._start_prompt_automation()
                    self._record_controller_event("NEW_CYCLE_STARTED")
                else:
                    self._record_controller_event("NEW_CYCLE_SKIPPED_PAUSED")
    
    def toggle_pause(self):
        """Toggle pause."""
        if self.ui.countdown_service.is_active():
            self.ui.countdown_service.toggle_pause()
            self._record_controller_event("PAUSE_TOGGLED", {"paused": self.ui.countdown_service.is_paused()})
    
    def is_started(self) -> bool:
        """Check if started."""
        return self._started
    
    def _validate_start_prerequisites(self) -> bool:
        """Validate prerequisites."""
        coords = self.ui.get_coords()
        if not all(key in coords for key in ["input", "submit", "accept"]):
            return False
        
        timers = self.ui.get_timers()
        if any(timer <= 0 for timer in timers):
            return False
        
        if len(self.ui.prompts) == 0:
            return False
        
        return True
    
    def _start_automation_thread(self):
        """Start automation thread."""
        def automation_worker():
            try:
                self._record_controller_event("AUTOMATION_THREAD_STARTED")
                # Simulate automation process
                time.sleep(0.1)  # Brief delay to simulate processing
                self._record_controller_event("AUTOMATION_THREAD_COMPLETED")
            except Exception as e:
                self._record_controller_event("AUTOMATION_THREAD_ERROR", {"error": str(e)})
        
        thread = threading.Thread(target=automation_worker, daemon=True)
        thread.start()
    
    def _start_prompt_automation(self):
        """Start prompt automation."""
        def prompt_worker():
            try:
                self._record_controller_event("PROMPT_AUTOMATION_STARTED")
                # Simulate single prompt automation
                time.sleep(0.1)
                self._record_controller_event("PROMPT_AUTOMATION_COMPLETED")
            except Exception as e:
                self._record_controller_event("PROMPT_AUTOMATION_ERROR", {"error": str(e)})
        
        thread = threading.Thread(target=prompt_worker, daemon=True)
        thread.start()
    
    def _reset_automation_state(self):
        """Reset automation state."""
        self._started = False
        self.ui.current_prompt_index = 0
        self._prompts_locked = False
    
    def _stop_countdown_if_active(self):
        """Stop countdown if active."""
        if self.ui.countdown_service.is_active():
            self.ui.countdown_service.stop()
    
    def _record_controller_event(self, event_type: str, data: Dict[str, Any] = None):
        """Record controller event."""
        self.controller_events.append({
            "timestamp": time.time(),
            "event": event_type,
            "data": data or {}
        })

# =============================================================================
# TEST SCENARIOS
# =============================================================================

class AutomationTestScenario:
    """Base class for automation test scenarios."""
    
    def __init__(self, name: str):
        self.name = name
        self.results = {}
        
    def setup(self) -> Tuple[VirtualUI, VirtualSessionController]:
        """Setup test environment."""
        raise NotImplementedError
        
    def run(self) -> Dict[str, Any]:
        """Run the test scenario."""
        raise NotImplementedError
        
    def analyze(self) -> Dict[str, Any]:
        """Analyze test results."""
        raise NotImplementedError

class PauseResumeTest(AutomationTestScenario):
    """Test pause/resume functionality."""
    
    def __init__(self):
        super().__init__("Pause/Resume Functionality Test")
        
    def setup(self) -> Tuple[VirtualUI, VirtualSessionController]:
        """Setup test environment."""
        prompts = [f"Test prompt {i}" for i in range(1, 4)]
        coordinates = VirtualCoordinates()
        timers = VirtualTimers(start_delay=1.0, main_wait=3.0, cooldown=1.0, get_ready_delay=1.0)
        
        ui = VirtualUI(prompts, coordinates, timers)
        controller = VirtualSessionController(ui)
        
        return ui, controller
    
    def run(self) -> Dict[str, Any]:
        """Run pause/resume test."""
        ui, controller = self.setup()
        
        # Start automation
        controller.start_automation()
        time.sleep(0.5)
        
        # Start a countdown
        result = ui.countdown(5.0, "Test countdown")
        time.sleep(1.0)
        
        # Pause the countdown
        controller.toggle_pause()
        time.sleep(2.0)
        
        # Resume the countdown
        controller.toggle_pause()
        time.sleep(2.0)
        
        # Click Next while paused
        controller.toggle_pause()  # Pause again
        controller.next_prompt()
        time.sleep(1.0)
        
        # Resume and continue
        controller.toggle_pause()
        time.sleep(2.0)
        
        # Stop automation
        controller.stop_automation()
        
        # Wait a bit for any final processing
        time.sleep(0.5)
        
        return {
            "ui": ui,
            "controller": controller,
            "countdown_data": ui.countdown_service.get_test_data()
        }
    
    def analyze(self) -> Dict[str, Any]:
        """Analyze pause/resume test results."""
        results = self.run()
        ui = results["ui"]
        controller = results["controller"]
        countdown_data = results["countdown_data"]
        
        # Analyze countdown behavior
        display_updates = countdown_data["display_updates"]
        state_changes = countdown_data["state_changes"]
        
        # Check if time was preserved during pause
        paused_updates = [u for u in display_updates if u["paused"]]
        non_paused_updates = [u for u in display_updates if not u["paused"]]
        
        # Check if new cycles were started when paused
        controller_events = controller.controller_events
        new_cycle_events = [e for e in controller_events if "NEW_CYCLE" in e["event"]]
        
        # Check if pause actually worked by looking at state changes
        pause_states = [s for s in state_changes if s["state"] == "PAUSED"]
        resume_states = [s for s in state_changes if s["state"] == "RESUMED"]
        
        analysis = {
            "pause_worked": len(pause_states) > 0,
            "time_preserved": countdown_data["final_remaining"] > 0,  # Time was preserved if not 0
            "new_cycles_when_paused": any("SKIPPED_PAUSED" in e["event"] for e in new_cycle_events),
            "total_cycles_started": len([e for e in new_cycle_events if "STARTED" in e["event"]]),
            "state_changes": [e["state"] for e in state_changes],
            "final_remaining": countdown_data["final_remaining"],
            "pause_count": len(pause_states),
            "resume_count": len(resume_states)
        }
        
        return analysis

class NextButtonPauseTest(AutomationTestScenario):
    """Test Next button behavior when paused."""
    
    def __init__(self):
        super().__init__("Next Button Pause Test")
        
    def setup(self) -> Tuple[VirtualUI, VirtualSessionController]:
        """Setup test environment."""
        prompts = [f"Test prompt {i}" for i in range(1, 4)]
        coordinates = VirtualCoordinates()
        timers = VirtualTimers(start_delay=1.0, main_wait=2.0, cooldown=1.0, get_ready_delay=1.0)
        
        ui = VirtualUI(prompts, coordinates, timers)
        controller = VirtualSessionController(ui)
        
        return ui, controller
    
    def run(self) -> Dict[str, Any]:
        """Run Next button pause test."""
        ui, controller = self.setup()
        
        # Start automation
        controller.start_automation()
        time.sleep(0.5)
        
        # Start countdown and pause it
        ui.countdown(10.0, "Long countdown")
        time.sleep(1.0)
        controller.toggle_pause()  # Pause
        time.sleep(0.5)
        
        # Click Next multiple times while paused
        for i in range(3):
            controller.next_prompt()
            time.sleep(0.2)
        
        # Resume and let it complete
        controller.toggle_pause()  # Resume
        time.sleep(2.0)
        
        # Stop automation
        controller.stop_automation()
        
        # Wait a bit for any final processing
        time.sleep(0.5)
        
        return {
            "ui": ui,
            "controller": controller
        }
    
    def analyze(self) -> Dict[str, Any]:
        """Analyze Next button pause test results."""
        results = self.run()
        controller = results["controller"]
        
        # Analyze controller events
        events = controller.controller_events
        new_cycle_events = [e for e in events if "NEW_CYCLE" in e["event"]]
        
        # Count how many cycles were started vs skipped
        cycles_started = len([e for e in new_cycle_events if "STARTED" in e["event"]])
        cycles_skipped = len([e for e in new_cycle_events if "SKIPPED_PAUSED" in e["event"]])
        
        analysis = {
            "total_next_clicks": 3,
            "cycles_started": cycles_started,
            "cycles_skipped_paused": cycles_skipped,
            "correct_behavior": cycles_started == 0 and cycles_skipped >= 1,  # At least one should be skipped
            "final_prompt_index": results["ui"].current_prompt_index,
            "prompt_advanced": results["ui"].current_prompt_index > 0
        }
        
        return analysis

# =============================================================================
# TEST RUNNER
# =============================================================================

class AutomationTestRunner:
    """Test runner for automation scenarios."""
    
    def __init__(self):
        self.scenarios = []
        self.results = {}
        
    def add_scenario(self, scenario: AutomationTestScenario):
        """Add a test scenario."""
        self.scenarios.append(scenario)
        
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test scenarios."""
        print("🧪 RUNNING AUTOMATION TEST SUITE")
        print("=" * 50)
        
        all_results = {}
        
        for scenario in self.scenarios:
            print(f"\n🔍 Running: {scenario.name}")
            print("-" * 30)
            
            try:
                analysis = scenario.analyze()
                all_results[scenario.name] = analysis
                
                # Print results
                self._print_analysis(scenario.name, analysis)
                
            except Exception as e:
                print(f"❌ Test failed: {e}")
                all_results[scenario.name] = {"error": str(e)}
        
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        self._print_summary(all_results)
        
        return all_results
    
    def _print_analysis(self, test_name: str, analysis: Dict[str, Any]):
        """Print test analysis."""
        if "error" in analysis:
            print(f"❌ {test_name}: FAILED - {analysis['error']}")
            return
            
        print(f"📋 {test_name} Results:")
        for key, value in analysis.items():
            if isinstance(value, bool):
                status = "✅" if value else "❌"
                print(f"   {status} {key}: {value}")
            else:
                print(f"   📊 {key}: {value}")
    
    def _print_summary(self, results: Dict[str, Any]):
        """Print test summary."""
        total_tests = len(results)
        passed_tests = 0
        failed_tests = 0
        
        for test_name, analysis in results.items():
            if "error" in analysis:
                failed_tests += 1
            else:
                # Check if test passed based on key indicators
                if "correct_behavior" in analysis:
                    if analysis["correct_behavior"]:
                        passed_tests += 1
                    else:
                        failed_tests += 1
                elif "pause_worked" in analysis and "time_preserved" in analysis:
                    if analysis["pause_worked"] and analysis["time_preserved"]:
                        passed_tests += 1
                    else:
                        failed_tests += 1
                else:
                    passed_tests += 1
        
        print(f"📈 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📊 Success Rate: {(passed_tests/total_tests)*100:.1f}%")

# =============================================================================
# MAIN TEST EXECUTION
# =============================================================================

def run_automation_tests():
    """Run the complete automation test suite."""
    runner = AutomationTestRunner()
    
    # Add test scenarios
    runner.add_scenario(PauseResumeTest())
    runner.add_scenario(NextButtonPauseTest())
    
    # Run all tests
    results = runner.run_all_tests()
    
    return results

if __name__ == "__main__":
    run_automation_tests()
