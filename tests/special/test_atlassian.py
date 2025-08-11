
import pytest
import requests
from livecheck.special.atlassian_rss import (
    get_latest_bitbucket_runner,
    get_latest_fisheye,
    get_latest_crucible,
    get_latest_crowd,
)

def test_bitbucket_runner(monkeypatch):
    sample_md = """
# Changelog

## 1.522.0 (2024-07-30)
- Update

## 1.521.0 (2024-07-15)
- Previous
"""
    monkeypatch.setattr(requests, "get", lambda url, timeout=10: type("Resp", (), {"text": sample_md, "raise_for_status": lambda self: None})())
    assert get_latest_bitbucket_runner() == "1.522.0"

def test_fisheye(monkeypatch):
    sample_rss = '''<?xml version="1.0"?><rss><channel><item><title>FishEye 4.8.0</title></item></channel></rss>'''
    monkeypatch.setattr(requests, "get", lambda url, timeout=10: type("Resp", (), {"text": sample_rss, "raise_for_status": lambda self: None})())
    assert get_latest_fisheye() == "4.8.0"

def test_crucible(monkeypatch):
    sample_rss = '''<?xml version="1.0"?><rss><channel><item><title>Crucible 4.8.0</title></item></channel></rss>'''
    monkeypatch.setattr(requests, "get", lambda url, timeout=10: type("Resp", (), {"text": sample_rss, "raise_for_status": lambda self: None})())
    assert get_latest_crucible() == "4.8.0"

def test_crowd(monkeypatch):
    sample_rss = '''<?xml version="1.0"?><rss><channel><item><title>Crowd 5.2.0</title></item></channel></rss>'''
    monkeypatch.setattr(requests, "get", lambda url, timeout=10: type("Resp", (), {"text": sample_rss, "raise_for_status": lambda self: None})())
    assert get_latest_crowd() == "5.2.0"
