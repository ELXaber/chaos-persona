# test_suite.py
import orchestrator
import paradox_oscillator as cpol
import adaptive_reasoning as arl

def test_basic_paradox():
    """Test: Classic liar paradox"""
    result = orchestrator.system_step("This statement is false.", "high")
    assert result['status'] == 'UNDECIDABLE'
    print("✅ Basic paradox test passed")

def test_memory_persistence():
    """Test: History maintained across calls"""
    orchestrator.system_step("Hello", "low")
    orchestrator.system_step("Paradox 1", "high")
    orchestrator.system_step("Paradox 2", "high")
    
    kernel = orchestrator.shared_memory['cpol_instance']
    assert len(kernel.history) > 1
    print(f"✅ Memory persistence: {len(kernel.history)} states retained")

# Run all tests
test_basic_paradox()
test_memory_persistence()
# ... more tests