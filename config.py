import configparser

def load_config(file_path='config.ini'):
    """Load configuration settings from an INI file into a nested dictionary."""
    config = configparser.ConfigParser()
    config.read(file_path)

    # Converting to a nested dictionary
    config_dict = {section: dict(config.items(section)) for section in config.sections()}

    return config_dict

config = load_config()