import json
import re
import numpy as np

from .redis import rd, rd_experiment_key

schemas = dict()

def validate_schema(schema):
    return 'result' not in schema and 'variant' not in schema

class SchemaViolationError(RuntimeError):
    pass

def encode_input_point(schema, form_data, variant, result):
    try:
        features = {
            feature_name: form_data[feature_name]
            for feature_name in schema.keys()
        }
        features['variant'] = variant
        features['result'] = result
        return features
    except KeyError as err:
        raise SchemaViolationError(f"Required feature {str(err)} is missing.")

def store_experiment_schema(experiment_uuid_hex, schema):
    rd.set(rd_experiment_key(experiment_uuid_hex, 'schema'), json.dumps(schema))

def get_experiment_schema(experiment_uuid_hex):
    return json.loads(rd.get(rd_experiment_key(experiment_uuid_hex, 'schema')) or '{}')


def _data_dimension(schema):
    return len(schema) # TODO will change

def _interpret_with_type(type_name, value, name):
    if type_name == "numeric":
        try:
            return float(value)
        except ValueError:
            raise SchemaViolationError(f"Field {name} was declared as numeric but {value} could not be interpreted as a float.")
    else:
        raise SchemaViolationError(f"Unknown type {type_name} for field {name}.")

def process_json_blobs(experiment_uuid_hex, json_blobs):
    schema = get_experiment_schema(experiment_uuid_hex)
    data_dim = _data_dimension(schema)
    n = len(json_blobs)
    X = np.ndarray((n, data_dim))
    y = np.ndarray((n,))

    front_index = 0
    back_index = -1
    for json_blob in json_blobs:
        obj = json.loads(json_blob)

        variant, result = obj['variant'], obj['result']
        del obj['variant']
        del obj['result']
        # TODO single point of truth for these strings
        # Sort points by variant so that there is a single boundary between
        # contiguous memory ranges for later processing that operates independly
        # on these sets
        if variant == 'a':
            row = front_index
            front_index += 1
        elif variant == 'b':
            row = back_index
            back_index -= 1

        y[row] = result == 'success'

        for col, (name, type_name) in enumerate(schema.items()):
            if name not in obj:
                raise SchemaViolationError(f"Required field {name} is missing from data")
            else:
                X[row, col] = _interpret_with_type(type_name, obj[name], name)

    return X, y, front_index
