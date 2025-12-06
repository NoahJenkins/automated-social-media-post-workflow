#!/usr/bin/env python3
"""
Test script to validate dev container configuration files exist and are properly formatted.
"""
import json
import os
import sys


def remove_json_comments(content):
    """Remove // style comments from JSON content."""
    lines = content.split('\n')
    cleaned_lines = []
    for line in lines:
        if '//' in line:
            before_comment = line.split('//')[0].strip()
            if before_comment:
                cleaned_lines.append(before_comment)
        else:
            cleaned_lines.append(line)
    return '\n'.join(cleaned_lines)


def test_devcontainer_exists():
    """Test that .devcontainer directory exists."""
    devcontainer_dir = ".devcontainer"
    assert os.path.isdir(devcontainer_dir), f"{devcontainer_dir} directory does not exist"
    print(f"✓ {devcontainer_dir} directory exists")


def test_devcontainer_json_exists():
    """Test that devcontainer.json exists."""
    devcontainer_json = ".devcontainer/devcontainer.json"
    assert os.path.isfile(devcontainer_json), f"{devcontainer_json} does not exist"
    print(f"✓ {devcontainer_json} exists")


def test_dockerfile_exists():
    """Test that Dockerfile exists."""
    dockerfile = ".devcontainer/Dockerfile"
    assert os.path.isfile(dockerfile), f"{dockerfile} does not exist"
    print(f"✓ {dockerfile} exists")


def test_devcontainer_json_valid():
    """Test that devcontainer.json is valid JSON (with comments removed)."""
    devcontainer_json = ".devcontainer/devcontainer.json"
    
    with open(devcontainer_json, 'r') as f:
        content = f.read()
    
    cleaned_content = remove_json_comments(content)
    
    # Try to parse as JSON
    try:
        json.loads(cleaned_content)
        print(f"✓ {devcontainer_json} is valid JSON (JSONC)")
    except json.JSONDecodeError as e:
        print(f"✗ {devcontainer_json} has JSON syntax error: {e}")
        raise


def test_devcontainer_json_has_required_fields():
    """Test that devcontainer.json has required fields."""
    devcontainer_json = ".devcontainer/devcontainer.json"
    
    with open(devcontainer_json, 'r') as f:
        content = f.read()
    
    cleaned_content = remove_json_comments(content)
    config = json.loads(cleaned_content)
    
    # Check required fields
    assert 'name' in config, "devcontainer.json missing 'name' field"
    assert 'build' in config or 'image' in config, "devcontainer.json must have 'build' or 'image' field"
    
    if 'build' in config:
        assert 'dockerfile' in config['build'], "build must specify 'dockerfile'"
    
    print(f"✓ {devcontainer_json} has required fields")


def test_dockerfile_has_from():
    """Test that Dockerfile has a FROM instruction."""
    dockerfile = ".devcontainer/Dockerfile"
    
    with open(dockerfile, 'r') as f:
        content = f.read()
    
    # Check for FROM instruction
    assert 'FROM' in content, "Dockerfile must have a FROM instruction"
    print(f"✓ {dockerfile} has FROM instruction")


def main():
    """Run all tests."""
    tests = [
        test_devcontainer_exists,
        test_devcontainer_json_exists,
        test_dockerfile_exists,
        test_devcontainer_json_valid,
        test_devcontainer_json_has_required_fields,
        test_dockerfile_has_from,
    ]
    
    print("Running dev container configuration tests...\n")
    
    failed = False
    for test in tests:
        try:
            test()
        except (AssertionError, Exception) as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed = True
    
    if not failed:
        print("\n✓ All dev container configuration tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
