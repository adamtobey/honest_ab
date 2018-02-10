# Standin before integrating distributed regression

schemas = dict()

# TODO
def store_experiment_schema(experiment_id, schema):
    schemas[experiment_id] = schema

def get_experiment_schema(experiment_id):
    return schemas[experiment_id]

def validate_schema(schema):
    return True
