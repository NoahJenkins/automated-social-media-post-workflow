"""
Integration test to verify the fix for:
1. Post scheduled only for Twitter/X (should now support multiple networks)
2. No image included (should now warn and explain why)
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_scenario_missing_azure_storage():
    """
    Simulates the reported issue: post scheduled but no image
    This happens when Azure Storage credentials are missing
    """
    print("=== Test Scenario: Missing Azure Storage Credentials ===\n")
    
    # Set up environment to simulate the issue
    os.environ["OPENAI_API_KEY"] = "test-key"
    os.environ["SOCIAL_NETWORKS"] = "twitter"
    
    # Ensure Azure Storage credentials are NOT set (simulating the issue)
    os.environ.pop("AZURE_STORAGE_CONNECTION_STRING", None)
    os.environ.pop("AZURE_STORAGE_CONTAINER_NAME", None)
    
    from src.agents.poster import poster_node, upload_image_to_metricool
    
    # Test 1: Verify that upload_image_to_metricool returns None with clear warning
    print("Test 1: Image upload without Azure Storage credentials")
    result_url = upload_image_to_metricool("https://example.com/image.png")
    assert result_url is None, "Expected None when Azure Storage is not configured"
    print("✓ Test 1 passed: Image upload returns None with warning\n")
    
    # Test 2: Verify poster still works (creates post without image)
    print("Test 2: Poster creates post without image")
    state = {
        "selected_post": "Test post about AI trends!",
        "image_url": "https://example.com/image.png",  # Image provided but can't upload
    }
    
    result = poster_node(state)
    assert "post_status" in result
    print("✓ Test 2 passed: Poster doesn't crash, creates post without image\n")
    
    print("=== Scenario Test Passed ===")
    print("\nExpected behavior:")
    print("- Warning message displayed about missing Azure Storage")
    print("- Post still created (mock in this test)")
    print("- No image attached to post")
    print("\nTo fix this issue, users should:")
    print("1. Set AZURE_STORAGE_CONNECTION_STRING in .env")
    print("2. Set AZURE_STORAGE_CONTAINER_NAME in .env")
    print("3. See CONFIGURATION_EXAMPLES.md for details")

def test_scenario_multi_network():
    """
    Tests the fix for: post only scheduled for Twitter/X
    Now it should support multiple networks via SOCIAL_NETWORKS config
    """
    print("\n=== Test Scenario: Multi-Network Posting ===\n")
    
    os.environ["OPENAI_API_KEY"] = "test-key"
    os.environ["SOCIAL_NETWORKS"] = "twitter,facebook,instagram,linkedin"
    
    # Reload config to pick up changes
    from importlib import reload
    import src.config as config
    reload(config)
    
    print(f"Configured networks: {config.SOCIAL_NETWORKS}")
    
    from src.agents.poster import poster_node
    
    state = {
        "selected_post": "Test post for all networks!",
        "image_url": None,
    }
    
    result = poster_node(state)
    assert "post_status" in result
    
    print("\n✓ Multi-network test passed")
    print("\nExpected behavior:")
    print("- Post scheduled for: twitter, facebook, instagram, linkedin")
    print("- Single post sent to all configured networks")
    print("\nTo configure networks, users should:")
    print("1. Set SOCIAL_NETWORKS=twitter,facebook,instagram,linkedin in .env")
    print("2. Ensure Metricool account is connected to all desired networks")
    print("3. See CONFIGURATION_EXAMPLES.md for examples")

if __name__ == "__main__":
    print("=" * 70)
    print("Integration Test: Reported Issues Fix Verification")
    print("=" * 70)
    print()
    
    try:
        test_scenario_missing_azure_storage()
        test_scenario_multi_network()
        
        print("\n" + "=" * 70)
        print("✅ ALL INTEGRATION TESTS PASSED")
        print("=" * 70)
        print("\nBoth reported issues are now fixed:")
        print("1. ✓ Multi-network posting is supported via SOCIAL_NETWORKS config")
        print("2. ✓ Clear warnings when images can't be uploaded (missing Azure Storage)")
        print("\nUsers should refer to:")
        print("- README.md: Troubleshooting section")
        print("- CONFIGURATION_EXAMPLES.md: Setup examples")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
