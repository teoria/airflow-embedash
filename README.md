# Airflow Embedash

A Python package for embedding dashboards in Apache Airflow UI. This plugin allows you to easily integrate Metabase, Datadog and Grafana dashboards into your Airflow environment, providing a seamless way to view data visualizations alongside your workflows.

## Features

- **Easy Dashboard Integration**: Embed Metabase dashboards directly into Apache Airflow UI
- **Flexible Configuration**: Customize menu labels and authentication tokens
- **Multiple Airflow Versions Support**: Compatible with Airflow 2.x and 3.x
- **Secure Access**: Supports Metabase token-based authentication for private dashboards

## Installation

Install the package using pip:

```bash
pip install airflow-embedash
```

Or in development mode:

```bash
pip install -e .
```

## Usage

### Basic Setup

1. **Configure Metabase Settings**: Set the required environment variables or Airflow connections:
   - `embeded_dashboards_metabase_token`: Your Metabase API token for private dashboards 

2. **Configure Menu Label**: 
   - Default menu label is "Dashboards"
   - Override by setting the `embeded_dashboards_menu_label` environment variable
 

## Package Structure

```
airflow_embedash/
├── __init__.py          # Package initialization
├── plugin/              # Plugin implementation directory
│   ├── __init__.py      # Plugin entry point
│   ├── airflow2.py      # Airflow 2.x compatibility layer
│   └── templates/       # HTML templates for dashboard views
│       ├── add_dashboard.html  # Add dashboard form
│       ├── edit_dashboard.html # Edit dashboard form
│       ├── settings.html       # Settings view
│       ├── view_not_set_up.html # Not configured view
│       └── view.html          # Main dashboard view
└── plugin/__init__.py   # Plugin initialization
```

## Development

To contribute to this project:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Ensure all tests pass:
   ```bash
   make test
   ```
5. Submit a pull request

### Development Setup

The project includes development containers and Docker configurations:

1. **Using Docker**:
   ```bash
   docker-compose up -d
   ```

2. **Local Development**:
   - Install development dependencies: `pip install -e ".[dev]"`
   - Run tests: `make test`

## Configuration Options

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `embeded_dashboards_metabase_token` | Metabase API token for private dashboards | Optional | 
| `embeded_dashboards_menu_label` | Custom menu label in Airflow UI | Optional |
 

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## License

This project is licensed under the MIT License.