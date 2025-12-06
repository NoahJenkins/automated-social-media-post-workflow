"""
Test the poster node to verify post confirmation logic works correctly.
This test verifies the response parsing and state updates.
"""
import sys
import os
import tempfile
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.poster import poster_node

def test_poster_with_mock_credentials():
    """Test poster with missing credentials to verify mock behavior"""
    print("Test 1: Poster with no API token")
    state = {
        "selected_post": "Test post about tech trends!",
        "image_url": None,
    }
    
    result = poster_node(state)
    
    print(f"Result: {result}")
    assert "post_status" in result
    assert "post_id" in result
    assert "post_scheduled" in result
    assert result["post_id"] is None
    assert result["post_scheduled"] is False
    print("✓ Test 1 passed: Mock posting works correctly with missing credentials\n")


def test_poster_state_updates():
    """Test that poster returns all expected state fields"""
    print("Test 2: Verify all state fields are returned")
    state = {
        "selected_post": "Another test post!",
        "image_url": None,
    }
    
    result = poster_node(state)
    
    required_fields = ["post_status", "post_id", "post_scheduled"]
    for field in required_fields:
        assert field in result, f"Missing required field: {field}"
    
    print(f"✓ Test 2 passed: All required fields present: {list(result.keys())}\n")


def test_poster_with_image():
    """Test poster with image to verify image handling"""
    print("Test 3: Poster with image (mock)")
    
    # Create a temporary image file for testing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.png', delete=False) as tmp_file:
        tmp_file.write("dummy")
        tmp_image_path = tmp_file.name
    
    try:
        state = {
            "selected_post": "Post with an image!",
            "image_url": tmp_image_path,
        }
        
        result = poster_node(state)
        
        print(f"Result: {result}")
        assert "post_status" in result
        print("✓ Test 3 passed: Image handling doesn't crash\n")
    finally:
        # Cleanup
        if os.path.exists(tmp_image_path):
            os.remove(tmp_image_path)


if __name__ == "__main__":
    print("=== Testing Poster Node ===\n")
    
    # Set required env vars for config
    os.environ["OPENAI_API_KEY"] = "test-key"
    
    try:
        test_poster_with_mock_credentials()
        test_poster_state_updates()
        test_poster_with_image()
        
        print("=== All Tests Passed! ===")
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
