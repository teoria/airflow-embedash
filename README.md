# Airflow Embedash

A Python package for embedding dashboards in Apache Airflow.

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

Create new dashboards
 
### Variable

The default menu label is "Dashboards" but can be changed setup `embeded_dashboards_menu_label`variable.	 
	
For private dashboars need metabase token `embeded_dashboards_metabase_token`

## Package Structure

- `src/` - Source code directory
  - `__init__.py` - Package initialization
  - `airflow_embeded_dashboards.py` - Main module with the main function

## Development

To contribute to this project:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.