from pathlib import Path


def test_legacy_prompt_file_has_been_removed():
    assert not Path('prompts.py').exists()
