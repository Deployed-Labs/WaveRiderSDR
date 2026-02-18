# Contributing to WaveRider SDR

First off, thank you for considering contributing to WaveRider SDR! It's people like you that make WaveRider SDR such a great tool.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Style Guidelines](#style-guidelines)
- [Community](#community)

## Code of Conduct

This project and everyone participating in it is governed by our commitment to fostering an open and welcoming environment. By participating, you are expected to uphold high standards of conduct:

- **Be respectful** of differing viewpoints and experiences
- **Accept constructive criticism** gracefully
- **Focus on what is best** for the community
- **Show empathy** towards other community members

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include as many details as possible:

**Use the following template:**

```
**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. See error

**Expected behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**
 - OS: [e.g., Windows 10, macOS 12.0, Ubuntu 22.04]
 - Python Version: [e.g., 3.9.5]
 - WaveRider SDR Version: [e.g., 1.0.0]
 - SDR Hardware: [e.g., RTL-SDR Blog V3]

**Additional context**
Any other context about the problem.
```

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

- **Clear title** and description
- **Use case** - why is this enhancement needed?
- **Possible implementation** - if you have ideas
- **Alternative approaches** - other ways to achieve the goal

### Your First Code Contribution

Unsure where to begin? Look for issues tagged with:

- `good first issue` - Good for newcomers
- `help wanted` - Extra attention needed
- `documentation` - Improvements or additions to documentation

### Pull Requests

We actively welcome your pull requests:

1. Fork the repo and create your branch from `main`
2. If you've added code that should be tested, add tests
3. If you've changed APIs, update the documentation
4. Ensure the test suite passes
5. Make sure your code follows the style guidelines
6. Issue that pull request!

## Development Setup

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Git

### Setup Steps

```bash
# 1. Fork and clone the repository
git clone https://github.com/YOUR-USERNAME/WaveRiderSDR.git
cd WaveRiderSDR

# 2. Create a virtual environment (recommended)
python -m venv venv

# Activate virtual environment:
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 3. Install in development mode with all dependencies
pip install -e ".[all]"

# Or install specific feature sets:
pip install -e ".[desktop]"  # Desktop GUI only
pip install -e ".[web]"      # Web interface only
pip install -e ".[sdr]"      # SDR hardware support only

# 4. Run tests (when available)
python -m pytest

# 5. Run the application
python run.py
```

### Development Tools

**Recommended tools:**
- **Code Editor**: VS Code, PyCharm, or your favorite editor
- **Python Linters**: pylint, flake8
- **Formatters**: black, autopep8
- **Type Checkers**: mypy (optional but encouraged)

**VS Code Extensions:**
- Python
- Pylance
- Python Docstring Generator

## Pull Request Process

### Before Submitting

- [ ] Code follows style guidelines (see below)
- [ ] Self-reviewed the code
- [ ] Commented code, particularly in complex areas
- [ ] Updated documentation if needed
- [ ] Added tests that prove your fix/feature works
- [ ] Existing tests pass locally
- [ ] Added yourself to CONTRIBUTORS.md (optional)

### PR Guidelines

**Good PRs:**
- ✅ Single feature or fix per PR
- ✅ Clear, descriptive title
- ✅ Detailed description of changes
- ✅ Links to related issues
- ✅ Screenshots/GIFs for UI changes
- ✅ Clean commit history
- ✅ Updated documentation

**Avoid:**
- ❌ Mixing multiple features/fixes
- ❌ Large reformatting changes
- ❌ Breaking existing functionality
- ❌ Undocumented changes
- ❌ Commits with unclear messages

### PR Template

Use this template when creating your PR:

```markdown
## Description
Brief description of changes.

## Motivation and Context
Why is this change required? What problem does it solve?
Fixes #(issue number)

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to change)
- [ ] Documentation update

## How Has This Been Tested?
Describe the tests you ran and their results.

## Screenshots (if applicable):
Add screenshots to help explain your changes.

## Checklist:
- [ ] My code follows the style guidelines
- [ ] I have performed a self-review
- [ ] I have commented my code where needed
- [ ] I have updated the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix/feature works
- [ ] New and existing tests pass locally
```

## Style Guidelines

### Python Code Style

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with some modifications:

**General Guidelines:**
- **Indentation**: 4 spaces (no tabs)
- **Line Length**: 100 characters max (soft limit), 120 absolute max
- **Imports**: Organized in three groups (standard library, third-party, local)
- **Naming**:
  - `snake_case` for functions and variables
  - `PascalCase` for classes
  - `UPPER_CASE` for constants
  - Prefix private methods with `_`

**Example:**

```python
"""Module docstring describing the file."""

import sys
import os
from pathlib import Path

import numpy as np
from PyQt5.QtWidgets import QApplication

from waverider_common import SDRDevice

# Constants
DEFAULT_SAMPLE_RATE = 2.4e6
MAX_FFT_SIZE = 8192


class SignalProcessor:
    """Process signals from SDR devices.
    
    This class handles signal acquisition, processing, and analysis
    from various SDR hardware devices.
    
    Args:
        device: SDR device instance
        sample_rate: Sample rate in Hz (default: 2.4 MHz)
    """
    
    def __init__(self, device, sample_rate=DEFAULT_SAMPLE_RATE):
        """Initialize the signal processor."""
        self.device = device
        self.sample_rate = sample_rate
        self._buffer = []
    
    def process_samples(self, samples):
        """Process raw IQ samples.
        
        Args:
            samples: NumPy array of complex IQ samples
            
        Returns:
            Processed samples as NumPy array
        """
        # Apply windowing
        windowed = samples * np.hamming(len(samples))
        
        # Compute FFT
        spectrum = np.fft.fft(windowed)
        
        return spectrum
    
    def _internal_method(self):
        """Private method for internal use only."""
        pass
```

### Docstring Format

Use Google-style docstrings:

```python
def compute_fft(samples, fft_size=1024):
    """Compute FFT of samples.
    
    This function computes the Fast Fourier Transform of the input
    samples with optional windowing.
    
    Args:
        samples (np.ndarray): Input samples (complex or real)
        fft_size (int, optional): FFT size. Defaults to 1024.
    
    Returns:
        np.ndarray: FFT result as complex array
    
    Raises:
        ValueError: If samples array is empty
        
    Example:
        >>> samples = np.random.randn(1024)
        >>> spectrum = compute_fft(samples, fft_size=2048)
    """
    if len(samples) == 0:
        raise ValueError("Samples array cannot be empty")
    
    return np.fft.fft(samples, n=fft_size)
```

### Commit Messages

Good commit messages help understand the project history:

**Format:**
```
Type: Short summary (50 chars or less)

More detailed explanatory text, if necessary. Wrap it to about 72
characters. Explain the problem that this commit is solving, and why
you're solving it in this particular way.

- Bullet points are okay
- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")

Fixes #123
Closes #456
```

**Types:**
- `Add:` New feature or capability
- `Fix:` Bug fix
- `Update:` Improvements to existing features
- `Refactor:` Code restructuring without functionality change
- `Docs:` Documentation changes
- `Test:` Adding or updating tests
- `Chore:` Maintenance tasks, dependencies, etc.

**Examples:**
```
Add: Support for HackRF devices via SoapySDR

Implement HackRF device detection and connection using SoapySDR API.
Includes automatic device discovery and configuration.

- Add SoapySDR imports with conditional loading
- Implement HackRF-specific settings
- Update device detection to include HackRF
- Add documentation for HackRF setup

Fixes #42
```

### HTML/CSS/JavaScript

For web interface contributions:

- **HTML**: Use semantic HTML5
- **CSS**: Keep styles organized, use CSS variables for theming
- **JavaScript**: Use modern ES6+ syntax, avoid jQuery
- **Formatting**: 2-space indentation for HTML/CSS/JS

## Community

### Where to Ask Questions

- **GitHub Discussions**: For general questions and ideas
- **GitHub Issues**: For bug reports and feature requests
- **Pull Requests**: For code review and specific implementation questions

### Recognition

Contributors are recognized in several ways:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- GitHub contributor badge on the repository

### Release Process

Releases are managed by maintainers:
1. Version bump in relevant files
2. Update CHANGELOG.md
3. Create release tag
4. Build executables for all platforms
5. Publish to GitHub Releases
6. (Future) Publish to PyPI

## Questions?

Don't hesitate to ask questions! We're here to help:
- Open a [GitHub Discussion](https://github.com/1090mb/WaveRiderSDR/discussions)
- Check existing [Issues](https://github.com/1090mb/WaveRiderSDR/issues)
- Read the [Documentation](README.md)

---

**Thank you for contributing to WaveRider SDR! 🌊**
