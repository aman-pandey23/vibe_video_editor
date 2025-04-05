import yaml
from pathlib import Path

def load_config(config_path):
    """Load and validate configuration with path resolution"""
    with open(config_path) as f:
        config = yaml.safe_load(f)
    return _process_paths(config)

def _process_paths(config):
    # Convert string paths to Path objects and create directories
    if 'scene_detection' in config:
        sd = config['scene_detection']
        for key in ['output_dir', 'yaml_dir']:
            if key in sd:
                path = Path(sd[key])
                path.mkdir(parents=True, exist_ok=True)
                sd[key] = path  # Keep as Path object for later use
                
        # Convert input_path to Path but don't create parent dirs
        if 'input_path' in sd:
            sd['input_path'] = Path(sd['input_path'])
            
    return config