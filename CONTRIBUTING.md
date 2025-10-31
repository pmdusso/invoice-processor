# Contributing to Invoice Processor

Thank you for your interest in contributing to this project! This guide will help you get started.

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- Git
- OpenAI API key (for testing)

### Setup
```bash
# Fork and clone the repository
git clone https://github.com/yourusername/invoice-processor.git
cd invoice-processor

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy example configuration
cp .env.example .env
# Edit .env with your test API key
```

## 📋 Development Guidelines

### Code Style
- Follow PEP 8 style guidelines
- Use type hints for all functions
- Add comprehensive docstrings
- Keep functions focused and small

### Testing
```bash
# Run all tests
python test_invoice_processor.py
python test_provider_mapping.py

# Run with coverage (if installed)
coverage run test_invoice_processor.py
coverage report
```

### Adding New Features
1. Create a feature branch: `git checkout -b feature-name`
2. Write tests for your feature
3. Implement the feature
4. Update documentation
5. Submit a pull request

## 🔒 Security and Privacy

### NEVER Commit
- API keys or credentials
- Real invoice data
- Personal information
- Production logs

### Test Data
- Create synthetic test PDFs
- Use mock data for examples
- Sanitize all examples and documentation

## 📝 Pull Request Process

### Before Submitting
- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] Documentation is updated
- [ ] No sensitive data is included
- [ ] Commit messages are clear

### PR Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation
- [ ] Refactoring
- [ ] Performance

## Testing
- [ ] Added tests for new functionality
- [ ] All existing tests pass
- [ ] Manual testing completed

## Security
- [ ] No sensitive data exposed
- [ ] API keys properly handled
- [ ] Input validation added
```

## 🐛 Bug Reports

### Bug Report Template
```markdown
## Description
Clear description of the bug

## Steps to Reproduce
1. Step one
2. Step two
3. See error

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: [e.g., macOS 14.0]
- Python version: [e.g., 3.11]
- Dependencies: [output of pip freeze]

## Additional Context
Any other relevant information
```

## 💡 Feature Requests

### Feature Request Template
```markdown
## Problem Description
What problem does this solve?

## Proposed Solution
How should it work?

## Alternatives Considered
Other approaches you thought of

## Additional Context
Any other relevant information
```

## 🏗️ Project Structure

```
invoice-processor/
├── src/                    # Main source code
├── tests/                  # Test files
├── docs/                   # Documentation
├── examples/               # Usage examples
├── .github/                # GitHub workflows
├── requirements.txt        # Dependencies
├── .env.example           # Configuration template
└── README.md              # Project documentation
```

## 🎯 Areas for Contribution

### High Priority
- [ ] Additional PDF processing libraries support
- [ ] More currency conversion options
- [ ] Web interface for non-technical users
- [ ] Docker containerization

### Medium Priority
- [ ] Performance optimizations
- [ ] Additional export formats
- [ ] Integration with accounting software
- [ ] Mobile app interface

### Low Priority
- [ ] Additional language support
- [ ] Plugin system
- [ ] Cloud deployment options
- [ ] Advanced analytics dashboard

## 📖 Documentation

### Types of Documentation
- **README.md**: Project overview and quick start
- **SECURITY.md**: Security guidelines and best practices
- **CONTRIBUTING.md**: This file
- **Code comments**: Inline documentation
- **Docstrings**: Function and class documentation

### Writing Style
- Use clear, concise language
- Include code examples
- Add screenshots where helpful
- Keep documentation up to date

## 🤝 Community Guidelines

### Code of Conduct
- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Assume good intentions

### Communication
- Use GitHub issues for bugs and features
- Use discussions for questions and ideas
- Be patient with response times
- Help others when you can

## 🏆 Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes for significant contributions
- Project documentation for major features

## 📞 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and ideas
- **Documentation**: Check existing docs first
- **Examples**: Review usage examples

---

Thank you for contributing to the Invoice Processor project! Your contributions help make this tool better for everyone.
