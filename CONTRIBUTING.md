# Contributing to Eyegle v1.0

We appreciate your interest in contributing to Eyegle! This document provides guidelines for contributing to this advanced eye tracking project.

## 🤝 How to Contribute

### Reporting Bugs

1. **Check existing issues** first to avoid duplicates
2. **Use the bug report template** when creating new issues
3. **Provide detailed information**:
   - Operating system and version
   - Python version
   - Camera specifications
   - Steps to reproduce the issue
   - Expected vs actual behavior
   - Screenshots or error logs if applicable

### Suggesting Features

1. **Search existing feature requests** to avoid duplicates
2. **Use the feature request template**
3. **Provide detailed description**:
   - Use case and motivation
   - Proposed implementation approach
   - Potential impact on existing functionality

### Code Contributions

#### Setup Development Environment

1. **Fork the repository**
   ```bash
   git clone https://github.com/your-username/eyegle.git
   cd eyegle
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

#### Development Guidelines

- **Follow PEP 8** style guidelines
- **Write descriptive commit messages**
- **Add documentation** for new features
- **Include tests** when applicable
- **Keep changes focused** - one feature per PR

#### Code Style

```python
# Good example - clear, documented, type hints
def calculate_gaze_coordinates(
    eye_landmarks: List[np.ndarray], 
    screen_dimensions: Tuple[int, int]
) -> Tuple[int, int]:
    """
    Calculate screen coordinates from eye landmarks.
    
    Args:
        eye_landmarks: Detected eye landmark coordinates
        screen_dimensions: Screen width and height
        
    Returns:
        Tuple of (x, y) screen coordinates
    """
    # Implementation here
    pass
```

#### Pull Request Process

1. **Create feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes and commit**
   ```bash
   git add .
   git commit -m "feat: add new calibration algorithm"
   ```

3. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

4. **Create Pull Request**
   - Use descriptive title
   - Fill out the PR template
   - Link related issues
   - Request review from maintainers

## 📋 Development Areas

### Priority Areas for Contribution

1. **Performance Optimization**
   - GPU acceleration improvements
   - Memory usage optimization
   - Latency reduction techniques

2. **Cross-Platform Support**
   - macOS compatibility
   - Linux distribution support
   - ARM architecture optimization

3. **Accessibility Features**
   - Voice feedback integration
   - High contrast themes
   - Screen reader compatibility

4. **Advanced Calibration**
   - Multi-monitor support
   - Dynamic recalibration
   - User-specific adaptation algorithms

5. **Testing & Documentation**
   - Unit test coverage
   - Integration tests
   - API documentation
   - User tutorials

## 🧪 Testing

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test category
python -m pytest tests/unit/
python -m pytest tests/integration/

# Run with coverage
python -m pytest --cov=core --cov=ui --cov=utils
```

### Test Categories

- **Unit Tests**: Individual component functionality
- **Integration Tests**: Component interaction testing
- **Performance Tests**: Latency and accuracy benchmarks
- **UI Tests**: User interface automation tests

## 📖 Documentation

### Code Documentation

- Use **docstrings** for all functions and classes
- Follow **Google style** docstring format
- Include **type hints** for better IDE support
- Add **inline comments** for complex algorithms

### User Documentation

- Update **README.md** for user-facing changes
- Modify **USER_GUIDE.md** for new features
- Update **GESTURE_MAP.md** for new gestures
- Add **examples/** for common use cases

## 🏆 Recognition

Contributors are recognized in several ways:

- **CONTRIBUTORS.md** listing all contributors
- **Release notes** crediting feature contributors  
- **GitHub contributors graph** automatic recognition
- **Special mentions** for significant contributions

## 📞 Getting Help

- **GitHub Discussions**: Ask questions and discuss ideas
- **GitHub Issues**: Report bugs and request features
- **Developer Contact**: [Hitansh Parikh](https://github.com/hitanshparikh)
- **Organization**: [Hivizstudios](https://github.com/hivizstudios)

## 🔐 Security

For security-related issues, please email the maintainers directly rather than creating public issues.

---

**Thank you for contributing to Eyegle v1.0!**  
*Together, we're advancing accessible computing technology* 🚀