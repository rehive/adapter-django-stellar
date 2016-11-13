import os

# Check if debug variable is there to determine whether loaded
env_vars_loaded = os.environ.get('DEBUG', '')

# fallback for when env variables are not loaded:
if not env_vars_loaded:
    try:
        print('Loading keys from file...')
        current_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        parent_directory = os.path.split(current_directory)[0]
        parent_directory = os.path.split(parent_directory)[0]
        print(parent_directory)

        file_path = os.path.join(parent_directory, './.local.env')
        with open(file_path, 'r') as f:
            output = f.read()
            output = output.split('\n')

        for var in output:
            if var:
                k, v = var.split('=', maxsplit=1)
                os.environ.setdefault(k, v)
    except FileNotFoundError:
        print('environmental variables file not found')
        pass

# Add all project configurations that are stored in env variables:

# config
DEBUG = os.environ.get('DEBUG', '') in ['True', True, 'true']
TASK_QUEUE = os.environ.get('TASK_QUEUE', '') in ['True', True, 'true']

# secrets
SECRET_KEY = os.environ.get('DJANGO_SECRET', 'dvznxtu08$$a9jxjh=jkkswbe5-dw5+ea%4k((1k69ooi7d(hj')

# Get the platform URL for the adapter (Rehive)
REHIVE_API_URL = os.environ.get('REHIVE_API_URL', '')

# Get the admin token for platform requests (Rehive)
REHIVE_API_TOKEN = os.environ.get('REHIVE_API_TOKEN', '')

# TODO: Replace this with user accounts and tokens.
ADAPTER_SECRET_KEY = os.environ.get('ADAPTER_SECRET_KEY', 'secret')
BLOCKCYPHER_TOKEN = os.environ.get('BLOCKCYPHER_TOKEN', '')

# Separate secret as for blockcypher this is passed over http requests as a query parameter.
BLOCKCYPHER_ADAPTER_SECRET = os.environ.get('BLOCKCYPHER_ADAPTER_SECRET', '')
