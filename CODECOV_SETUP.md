# Codecov Setup Guide

This guide explains how to set up Codecov for the GGnet project to track code coverage across both backend and frontend components.

## Prerequisites

1. A GitHub repository with the GGnet project
2. A Codecov account (free tier available)

## Setup Steps

### 1. Create Codecov Account

1. Go to [codecov.io](https://codecov.io)
2. Sign up using your GitHub account
3. Authorize Codecov to access your repositories

### 2. Add Repository to Codecov

1. In your Codecov dashboard, click "Add a repository"
2. Select your GGnet repository
3. Copy the repository token (you'll need this for the GitHub secret)

### 3. Configure GitHub Secrets

1. Go to your GitHub repository
2. Navigate to Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Name: `CODECOV_TOKEN`
5. Value: Paste the token from step 2
6. Click "Add secret"

### 4. Verify Configuration

The project includes:
- `codecov.yml` - Configuration file for coverage settings
- Updated CI workflow with proper Codecov integration
- Coverage reporting for both backend (Python) and frontend (TypeScript/React)

## Coverage Configuration

### Backend Coverage
- **Tool**: pytest-cov
- **Output**: XML and HTML reports
- **Target**: 70% coverage
- **Threshold**: 5% decrease tolerance

### Frontend Coverage
- **Tool**: Vitest with v8 coverage
- **Output**: LCOV, JSON, HTML reports
- **Target**: 70% coverage
- **Threshold**: 5% decrease tolerance

## Files Generated

After running tests, the following coverage files are created:

### Backend
- `backend/coverage.xml` - XML format for CI
- `backend/htmlcov/` - HTML coverage report

### Frontend
- `frontend/coverage/lcov.info` - LCOV format for CI
- `frontend/coverage/coverage-final.json` - JSON format
- `frontend/coverage/index.html` - HTML coverage report

## Running Coverage Locally

### Backend
```bash
cd backend
pytest tests/ -v --cov=app --cov-report=xml --cov-report=html
```

### Frontend
```bash
cd frontend
npm run test:coverage
```

## Coverage Reports

- **CI Reports**: Automatically uploaded to Codecov on every push/PR
- **Local Reports**: Generated in `coverage/` directories
- **Web Dashboard**: Available at codecov.io for your repository

## Troubleshooting

### Common Issues

1. **"Token required" error**
   - Ensure `CODECOV_TOKEN` secret is set in GitHub
   - Verify the token is correct in Codecov dashboard

2. **Coverage files not found**
   - Check that tests are running with coverage enabled
   - Verify file paths in CI workflow match actual output

3. **Low coverage warnings**
   - Review the `codecov.yml` configuration
   - Adjust coverage targets if needed
   - Add more tests to improve coverage

### Configuration Files

- `codecov.yml` - Main configuration
- `.github/workflows/ci.yml` - CI integration
- `frontend/vite.config.ts` - Frontend test configuration
- `backend/pytest.ini` - Backend test configuration

## Best Practices

1. **Aim for meaningful coverage** - Focus on critical business logic
2. **Set realistic targets** - 70% is a good starting point
3. **Monitor trends** - Watch for coverage decreases over time
4. **Review reports** - Use coverage data to identify untested code
5. **Maintain quality** - Don't sacrifice test quality for coverage numbers
