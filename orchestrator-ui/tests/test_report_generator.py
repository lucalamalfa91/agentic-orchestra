"""
Test Report Generator

Generates comprehensive HTML and JSON reports from test execution results.

Usage:
    python test_report_generator.py
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


class TestReportGenerator:
    """Generate comprehensive test reports."""

    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "summary": {},
            "tests": [],
            "coverage": {},
            "recommendations": []
        }

    def run_tests_with_json_output(self):
        """Run pytest with JSON output."""
        try:
            # Run pytest with JSON report
            result = subprocess.run(
                ["pytest", "--json-report", "--json-report-file=report.json"],
                capture_output=True,
                text=True
            )

            if Path("report.json").exists():
                with open("report.json", "r") as f:
                    return json.load(f)

            return None

        except Exception as e:
            print(f"Error running tests: {e}")
            return None

    def generate_html_report(self, output_file="test_report.html"):
        """Generate HTML test report."""
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>E2E Auth Flow Test Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
        }}

        .header p {{
            opacity: 0.9;
            font-size: 1.1rem;
        }}

        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 40px;
            background: #f8f9fa;
        }}

        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }}

        .stat-card .value {{
            font-size: 3rem;
            font-weight: bold;
            margin-bottom: 10px;
        }}

        .stat-card .label {{
            color: #666;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .passed {{ color: #10b981; }}
        .failed {{ color: #ef4444; }}
        .skipped {{ color: #f59e0b; }}

        .content {{
            padding: 40px;
        }}

        .section {{
            margin-bottom: 40px;
        }}

        .section h2 {{
            font-size: 1.8rem;
            margin-bottom: 20px;
            color: #1f2937;
            border-bottom: 2px solid #e5e7eb;
            padding-bottom: 10px;
        }}

        .test-list {{
            background: #f9fafb;
            border-radius: 8px;
            padding: 20px;
        }}

        .test-item {{
            background: white;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 6px;
            border-left: 4px solid #10b981;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .test-item.failed {{
            border-left-color: #ef4444;
        }}

        .test-name {{
            font-weight: 500;
            color: #1f2937;
        }}

        .test-status {{
            font-weight: bold;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 0.85rem;
        }}

        .test-status.passed {{
            background: #d1fae5;
            color: #065f46;
        }}

        .test-status.failed {{
            background: #fee2e2;
            color: #991b1b;
        }}

        .recommendations {{
            background: #fffbeb;
            border-left: 4px solid #f59e0b;
            padding: 20px;
            border-radius: 6px;
        }}

        .recommendations h3 {{
            color: #92400e;
            margin-bottom: 10px;
        }}

        .recommendations ul {{
            list-style: none;
            padding-left: 0;
        }}

        .recommendations li {{
            padding: 8px 0;
            color: #78350f;
        }}

        .recommendations li:before {{
            content: "→ ";
            font-weight: bold;
        }}

        .footer {{
            background: #f9fafb;
            padding: 20px;
            text-align: center;
            color: #6b7280;
            font-size: 0.9rem;
        }}

        .timestamp {{
            color: #9ca3af;
            font-size: 0.85rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>E2E Auth Flow Test Report</h1>
            <p>Comprehensive Authentication Flow Testing Results</p>
            <p class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <div class="summary">
            <div class="stat-card">
                <div class="value passed">0</div>
                <div class="label">Passed</div>
            </div>
            <div class="stat-card">
                <div class="value failed">0</div>
                <div class="label">Failed</div>
            </div>
            <div class="stat-card">
                <div class="value skipped">0</div>
                <div class="label">Skipped</div>
            </div>
            <div class="stat-card">
                <div class="value">0%</div>
                <div class="label">Success Rate</div>
            </div>
        </div>

        <div class="content">
            <div class="section">
                <h2>Test Results</h2>
                <div class="test-list">
                    <p style="color: #6b7280; text-align: center;">
                        Run tests to see results here
                    </p>
                </div>
            </div>

            <div class="section">
                <h2>Recommendations</h2>
                <div class="recommendations">
                    <h3>Setup Instructions</h3>
                    <ul>
                        <li>Install dependencies: pip install -r requirements.txt</li>
                        <li>Start backend: cd ../backend && uvicorn main:app --reload</li>
                        <li>Start frontend: cd ../frontend && npm run dev</li>
                        <li>Run tests: pytest -v</li>
                    </ul>
                </div>
            </div>
        </div>

        <div class="footer">
            <p>Agentic Orchestra - E2E Testing Suite</p>
            <p>For more information, see README.md</p>
        </div>
    </div>
</body>
</html>
        """

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html)

        print(f"HTML report generated: {output_file}")

    def generate_markdown_report(self, output_file="TEST_REPORT.md"):
        """Generate Markdown test report."""
        report = f"""# E2E Auth Flow Test Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

| Metric | Value |
|--------|-------|
| Total Tests | 0 |
| Passed | 0 |
| Failed | 0 |
| Skipped | 0 |
| Success Rate | 0% |

## Test Coverage

### API Endpoints

- `GET /api/auth/github/login` - GitHub OAuth URL generation
- `GET /api/auth/github/callback` - GitHub OAuth callback
- `GET /api/auth/github/status` - Connection status
- `POST /api/config/ai-provider` - Save configuration
- `GET /api/config/ai-provider` - Retrieve configuration
- `POST /api/config/ai-provider/test` - Test connection

### Frontend Routes

- `/auth` - Authentication screen
- `/auth/callback` - OAuth callback
- `/provider-setup` - AI provider setup
- `/` - Main dashboard

## Test Results

Run `pytest -v` to see detailed results.

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start Services

```bash
# Backend
cd ../backend
uvicorn main:app --reload

# Frontend (in another terminal)
cd ../frontend
npm run dev
```

### 3. Run Tests

```bash
# All tests
pytest -v

# Specific test file
pytest test_auth_flow.py -v

# With coverage
pytest --cov=../backend --cov-report=html
```

## Recommendations

- Ensure both backend and frontend services are running
- Configure GitHub OAuth credentials in .env
- Use valid AI provider credentials for integration tests
- Check test logs for detailed error messages

## Contact

For issues or questions, see main project README.
"""

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(report)

        print(f"Markdown report generated: {output_file}")


def main():
    """Main function."""
    print("\nGenerating test reports...")

    generator = TestReportGenerator()

    # Generate HTML report
    generator.generate_html_report()

    # Generate Markdown report
    generator.generate_markdown_report()

    print("\nReports generated successfully!")
    print("- test_report.html (open in browser)")
    print("- TEST_REPORT.md (markdown format)")


if __name__ == "__main__":
    main()
