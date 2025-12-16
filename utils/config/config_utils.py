import yaml

def load_config(config_path):
    """Load and validate configuration from YAML file"""
    with open(config_path) as f:
        config = yaml.safe_load(f)
    return config