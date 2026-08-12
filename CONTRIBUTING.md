# Contributing to token-sentry

Thank you for considering contributing to token-sentry! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what is best for the community
- Show empathy towards other community members

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in Issues
2. If not, create a new issue with:
   - Clear, descriptive title
   - Steps to reproduce
   - Expected vs actual behavior
   - Screenshots if applicable
   - Environment details (OS, Docker version, etc.)

### Suggesting Enhancements

1. Check if the enhancement has been suggested
2. Create an issue with:
   - Clear description of the enhancement
   - Use cases and benefits
   - Possible implementation approach

### Pull Requests

1. **Fork the repository**
   ```bash
   git clone https://github.com/yourusername/tokenhealth.git
   cd tokenhealth
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow existing code style
   - Add tests for new functionality
   - Update documentation as needed

4. **Test your changes**
   ```bash
   # Backend tests
   cd backend
   pytest tests -v

   # Frontend (if applicable)
   cd frontend
   npm run build
   ```

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

   Use conventional commit messages:
   - `feat:` new feature
   - `fix:` bug fix
   - `docs:` documentation changes
   - `test:` adding tests
   - `refactor:` code refactoring
   - `style:` formatting changes
   - `chore:` maintenance tasks

6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request**
   - Provide clear description of changes
   - Reference any related issues
   - Wait for review

## Development Setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

### Running Tests

```bash
# Backend
cd backend
pytest tests -v

# With coverage
pytest tests --cov=. --cov-report=html
```

## Code Style

### Python (Backend)

- Follow PEP 8
- Use type hints where appropriate
- Maximum line length: 100 characters
- Use docstrings for functions and classes

Example:
```python
def compute_risk_score(metrics: Dict[str, Any]) -> float:
    """
    Compute risk score from token metrics.

    Args:
        metrics: Dictionary containing token metrics

    Returns:
        Risk score between 0 and 100
    """
    pass
```

### JavaScript/React (Frontend)

- Use ES6+ features
- Prefer functional components with hooks
- Use descriptive variable names
- Add comments for complex logic

Example:
```javascript
const analyzeToken = async (contract) => {
  // Validate contract address
  if (!contract || contract.length !== 42) {
    throw new Error('Invalid contract address')
  }

  // Fetch analysis
  const response = await api.post('/health', { contract })
  return response.data
}
```

## Adding New Heuristics

To add a new risk heuristic:

1. **Add to `heuristics.py`**
   ```python
   def _check_new_heuristic(self, metrics: Dict[str, Any]) -> float:
       """Your heuristic description"""
       if condition:
           self.reasons.append({
               "id": "new_heuristic",
               "value": value,
               "contribution": risk_points,
               "note": "Explanation for user"
           })
           return risk_points
       return 0
   ```

2. **Call in `compute()` method**
   ```python
   total_risk += self._check_new_heuristic(metrics)
   ```

3. **Add tests in `backend/tests/`**
   ```python
   def test_new_heuristic(self):
       """Test new heuristic logic"""
       # Your test here
   ```

4. **Update README**
   - Add to heuristics table
   - Document risk impact and description

## Adding New Data Sources

1. Create a new module: `backend/data_sources/your_source.py`
2. Implement fetcher class:
   ```python
   class YourSourceFetcher:
       def fetch_token_data(self, contract: str) -> Dict[str, Any]:
           # Implementation
           pass
   ```
3. Add tests
4. Update documentation

## Project Structure Guidelines

```
backend/
├── app.py              # Main FastAPI app (routes only)
├── heuristics.py       # Risk scoring logic
├── graph_builder.py    # Graph construction
├── llm_agent.py        # LLM integration
├── data_sources/       # External API integrations
└── test_*.py          # Tests

frontend/
├── src/
│   ├── App.jsx         # Main component
│   ├── components/     # Reusable components
│   └── utils/          # Helper functions
```

## Questions?

- Open an issue for questions
- Check existing documentation
- Review closed issues and PRs

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
