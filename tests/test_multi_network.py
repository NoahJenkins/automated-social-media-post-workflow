"""
Test the poster node with multiple social networks configured
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_multi_network_posting():
    """Test poster with multiple networks configured"""
    print("=== Testing Multi-Network Posting ===\n")
    
    # Set required env vars
    os.environ["OPENAI_API_KEY"] = "test-key"
    os.environ["SOCIAL_NETWORKS"] = "twitter,facebook,instagram,linkedin"
    
    # Reload config to pick up new env vars
    from importlib import reload
    import src.config as config
    reload(config)
    
    print(f"Configured networks: {config.SOCIAL_NETWORKS}")
    assert config.SOCIAL_NETWORKS == ["twitter", "facebook", "instagram", "linkedin"]
    
    from src.agents.poster import poster_node
    
    state = {
        "selected_post": "Test post for multiple networks!",
        "image_url": None,
    }
    
    result = poster_node(state)
    
    print(f"\nResult: {result}")
    assert "post_status" in result
    assert "post_id" in result
    assert "post_scheduled" in result
    
    print("\n✅ Multi-network test passed!")

if __name__ == "__main__":
    test_multi_network_posting()
