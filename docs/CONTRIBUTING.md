# Contributing to SwarmDirector

We welcome contributions to SwarmDirector! This guide will help you get started with contributing to the project.

## 🤝 How to Contribute

### Types of Contributions

We welcome several types of contributions:

- **🐛 Bug Reports**: Help us identify and fix issues
- **✨ Feature Requests**: Suggest new functionality
- **📝 Documentation**: Improve or add documentation
- **🔧 Code Contributions**: Bug fixes, new features, improvements
- **🧪 Testing**: Add or improve test coverage
- **🎨 UI/UX**: Improve user interface and experience

## 🚀 Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/SwarmDirector.git
cd SwarmDirector

# Add upstream remote
git remote add upstream https://github.com/blopit/SwarmDirector.git
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt  # If available

# Set up pre-commit hooks (if available)
pre-commit install
```

### 3. Create a Branch

```bash
# Create and switch to a new branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b bugfix/issue-description
```

## 📋 Development Guidelines

### Code Style

We follow Python best practices and PEP 8:

```python
# Use type hints
def process_task(task: Task) -> TaskResult:
    """Process a task and return the result."""
    pass

# Use descriptive names
def calculate_agent_efficiency(agent: Agent, time_period: timedelta) -> float:
    pass

# Document your functions
def create_agent(name: str, agent_type: AgentType) -> Agent:
    """Create a new agent with the specified name and type.
    
    Args:
        name: The name of the agent
        agent_type: The type of agent to create
        
    Returns:
        The newly created agent instance
        
    Raises:
        ValueError: If name is empty or agent_type is invalid
    """
    pass
```

### Code Formatting

We use automated code formatting:

```bash
# Format code with Black
black src/ tests/

# Sort imports with isort
isort src/ tests/

# Check style with flake8
flake8 src/ tests/
```

### Testing Requirements

All contributions must include appropriate tests:

```python
# Example test structure
def test_agent_creation():
    """Test that agents are created correctly."""
    # Arrange
    agent_name = "Test Agent"
    agent_type = AgentType.WORKER
    
    # Act
    agent = create_agent(agent_name, agent_type)
    
    # Assert
    assert agent.name == agent_name
    assert agent.agent_type == agent_type
    assert agent.status == AgentStatus.IDLE
```

### Documentation

- Add docstrings to all public functions and classes
- Update relevant documentation files
- Include examples where helpful
- Use clear, concise language

## 🐛 Bug Reports

### Before Submitting

1. **Check existing issues** to avoid duplicates
2. **Test with the latest version** to ensure the bug still exists
3. **Gather information** about your environment

### Bug Report Template

```markdown
**Bug Description**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected Behavior**
A clear description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Environment:**
- OS: [e.g. macOS 12.0]
- Python Version: [e.g. 3.9.7]
- SwarmDirector Version: [e.g. 1.0.0]
- Browser: [e.g. Chrome 95.0] (if applicable)

**Additional Context**
Add any other context about the problem here.
```

## ✨ Feature Requests

### Before Submitting

1. **Check existing feature requests** to avoid duplicates
2. **Consider the scope** - is this aligned with project goals?
3. **Think about implementation** - how might this work?

### Feature Request Template

```markdown
**Feature Description**
A clear description of what you want to happen.

**Problem Statement**
What problem does this feature solve?

**Proposed Solution**
Describe the solution you'd like to see.

**Alternatives Considered**
Describe any alternative solutions you've considered.

**Additional Context**
Add any other context, mockups, or examples about the feature request.
```

## 🔧 Code Contributions

### Development Process

1. **Discuss first** for large changes (create an issue)
2. **Write tests** before implementing features
3. **Keep changes focused** - one feature/fix per PR
4. **Update documentation** as needed
5. **Test thoroughly** before submitting

### Pull Request Process

1. **Update your branch** with latest upstream changes:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run the test suite**:
   ```bash
   pytest tests/
   ```

3. **Check code style**:
   ```bash
   black --check src/ tests/
   flake8 src/ tests/
   ```

4. **Create pull request** with descriptive title and description

### Pull Request Template

```markdown
**Description**
Brief description of changes made.

**Type of Change**
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

**Testing**
- [ ] Tests pass locally
- [ ] New tests added for new functionality
- [ ] Manual testing completed

**Checklist**
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings introduced
```

## 🧪 Testing Guidelines

### Test Structure

```
tests/
├── test_agents/           # Agent-specific tests
├── test_models/           # Database model tests
├── test_api/              # API endpoint tests
├── test_utils/            # Utility function tests
├── fixtures/              # Test data and fixtures
└── integration/           # End-to-end tests
```

### Writing Tests

```python
import pytest
from src.swarm_director.models.agent import Agent, AgentType

class TestAgent:
    """Test cases for Agent model."""
    
    def test_agent_creation(self):
        """Test basic agent creation."""
        agent = Agent(name="Test Agent", agent_type=AgentType.WORKER)
        assert agent.name == "Test Agent"
        assert agent.agent_type == AgentType.WORKER
    
    def test_agent_validation(self):
        """Test agent validation rules."""
        with pytest.raises(ValueError):
            Agent(name="", agent_type=AgentType.WORKER)
    
    @pytest.fixture
    def sample_agent(self):
        """Fixture providing a sample agent."""
        return Agent(name="Sample Agent", agent_type=AgentType.WORKER)
```

### Test Coverage

- Aim for **80%+ code coverage**
- Test both **happy path** and **error cases**
- Include **integration tests** for complex workflows
- Mock external dependencies

## 📝 Documentation Contributions

### Documentation Types

- **API Documentation**: Document all endpoints and parameters
- **Architecture Documentation**: Explain system design and patterns
- **User Guides**: Help users accomplish specific tasks
- **Developer Guides**: Help contributors understand the codebase

### Documentation Style

- Use clear, concise language
- Include code examples
- Provide step-by-step instructions
- Keep documentation up-to-date with code changes

## 🔍 Code Review Process

### For Contributors

- **Respond promptly** to review feedback
- **Ask questions** if feedback is unclear
- **Make requested changes** in separate commits
- **Be open to suggestions** and learning opportunities

### Review Criteria

- **Functionality**: Does the code work as intended?
- **Testing**: Are there adequate tests?
- **Style**: Does it follow project conventions?
- **Documentation**: Is it properly documented?
- **Performance**: Are there any performance concerns?
- **Security**: Are there any security implications?

## 🏷️ Commit Guidelines

### Commit Message Format

```
type(scope): description

[optional body]

[optional footer]
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, etc.)
- **refactor**: Code refactoring
- **test**: Adding or modifying tests
- **chore**: Maintenance tasks

### Examples

```
feat(agents): add email agent with SMTP integration

Add EmailAgent class that integrates with Flask-Mail for sending emails.
Includes configuration for SMTP servers and template processing.

Closes #123
```

```
fix(database): resolve connection pool exhaustion

Fix issue where database connections were not being properly released,
causing connection pool exhaustion under high load.

Fixes #456
```

## 🚀 Release Process

### Versioning

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

- [ ] All tests pass
- [ ] Documentation updated
- [ ] Version number updated
- [ ] Changelog updated
- [ ] Release notes prepared

## 🆘 Getting Help

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and general discussion
- **Code Reviews**: Learning and improvement opportunities

### Resources

- **Documentation**: Check the `docs/` directory
- **Examples**: Review code in `examples/`
- **Tests**: Look at existing tests for patterns
- **Architecture**: Review `docs/architecture/`

## 🎉 Recognition

Contributors will be recognized in:

- **CONTRIBUTORS.md**: List of all contributors
- **Release Notes**: Major contributions highlighted
- **GitHub**: Contributor statistics and graphs

## 📄 License

By contributing to SwarmDirector, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to SwarmDirector! Your contributions help make this project better for everyone. 🚀
