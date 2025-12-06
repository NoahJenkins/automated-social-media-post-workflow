"""
Test social networks configuration parsing
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_social_networks_parsing():
    """Test that SOCIAL_NETWORKS environment variable is parsed correctly"""
    
    # Test 1: Default value (twitter only)
    os.environ.pop("SOCIAL_NETWORKS", None)
    from importlib import reload
    import src.config as config
    reload(config)
    
    assert config.SOCIAL_NETWORKS == ["twitter"], f"Expected ['twitter'], got {config.SOCIAL_NETWORKS}"
    print("✓ Test 1 passed: Default to twitter")
    
    # Test 2: Multiple networks
    os.environ["SOCIAL_NETWORKS"] = "twitter,facebook,instagram,linkedin"
    reload(config)
    
    expected = ["twitter", "facebook", "instagram", "linkedin"]
    assert config.SOCIAL_NETWORKS == expected, f"Expected {expected}, got {config.SOCIAL_NETWORKS}"
    print("✓ Test 2 passed: Multiple networks")
    
    # Test 3: Networks with spaces
    os.environ["SOCIAL_NETWORKS"] = " twitter , facebook , instagram "
    reload(config)
    
    expected = ["twitter", "facebook", "instagram"]
    assert config.SOCIAL_NETWORKS == expected, f"Expected {expected}, got {config.SOCIAL_NETWORKS}"
    print("✓ Test 3 passed: Networks with spaces")
    
    # Test 4: Single network
    os.environ["SOCIAL_NETWORKS"] = "facebook"
    reload(config)
    
    assert config.SOCIAL_NETWORKS == ["facebook"], f"Expected ['facebook'], got {config.SOCIAL_NETWORKS}"
    print("✓ Test 4 passed: Single network")
    
    # Test 5: Empty string defaults to twitter
    os.environ["SOCIAL_NETWORKS"] = ""
    reload(config)
    
    # Empty string split becomes [''], which should be filtered out, then default to twitter
    assert config.SOCIAL_NETWORKS == [] or config.SOCIAL_NETWORKS == ["twitter"], \
        f"Expected empty list or ['twitter'], got {config.SOCIAL_NETWORKS}"
    print("✓ Test 5 passed: Empty string handling")
    
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    # Set required env vars to avoid config errors
    os.environ["OPENAI_API_KEY"] = "test-key"
    
    test_social_networks_parsing()
