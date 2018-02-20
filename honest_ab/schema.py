import json
import re
import numpy as np

from .redis import rd, rd_experiment_key
from .experiment_constants import *

class SchemaViolationError(RuntimeError):
    pass

class InvalidSchemaError(RuntimeError):
    pass

class Schema(object):

    @staticmethod
    def initialize_from_form(experiment_uuid_hex, form_dict):
        schema_names = dict()
        schema_types = dict()
        for form_key, value in form_dict.items():
            # This pattern is coupled with experiment-schema_builder.js
            m = re.match("^schema_field_(\d+)_(name|type)", form_key)
            if m:
                schema_id, field_type = m.group(1, 2)
                if field_type == "name":
                    schema_names[schema_id] = value
                else:
                    schema_types[schema_id] = value

        schema_dict = {
            schema_names[s_id]: schema_types[s_id]
            for s_id in schema_names.keys()
        }

        if RESULT_KEY in schema_dict or VARIANT_KEY in schema_dict:
            raise InvalidSchemaError(f"{RESULT_KEY} and {VARIANT_KEY} are reserved names in the schema.")

        Schema(experiment_uuid_hex, schema_dict).save()

    @staticmethod
    def for_experiment(experiment_uuid_hex):
        # TODO Arrow serialization
        schema = json.loads(rd.get(rd_experiment_key(experiment_uuid_hex, 'schema')) or '{}')
        return Schema(experiment_uuid_hex, schema)

    def __init__(self, experiment_uuid_hex, schema_dict):
        self.eid = experiment_uuid_hex
        self.schema = schema_dict

    def dimension(self):
        return len(self.schema) # TODO

    def save(self):
        rd.set(rd_experiment_key(self.eid, 'schema'), json.dumps(self.schema))

    def as_json(self):
        return self.schema

    def encode_input_point(self, form_data, variant, result):
        try:
            features = {
                feature_name: form_data[feature_name]
                for feature_name in self.schema.keys()
            }
            features[VARIANT_KEY] = variant
            features[RESULT_KEY] = result
            return features
        except KeyError as err:
            raise SchemaViolationError(f"Required feature {str(err)} is missing.")

    def _interpret_with_type(self, type_name, value, name):
        if type_name == NUMERIC_TYPE:
            try:
                return float(value)
            except ValueError:
                raise SchemaViolationError(f"Field {name} was declared as numeric but {value} could not be interpreted as a float.")
        else:
            raise SchemaViolationError(f"Unknown type {type_name} for field {name}.")

    def encode_batch_by_variant(self, json_blobs):
        N = len(json_blobs)
        X = np.ndarray((N, self.dimension()))
        y = np.ndarray((N,))

        front_index = 0
        back_index = -1
        for json_blob in json_blobs:
            obj = json.loads(json_blob)

            variant, result = obj[VARIANT_KEY], obj[RESULT_KEY]
            del obj[VARIANT_KEY]
            del obj[RESULT_KEY]

            # Sort points by variant so that there is a single boundary between
            # contiguous memory ranges for later processing that operates independly
            # on these sets
            if variant == VARIANTS[0]:
                row = front_index
                front_index += 1
            elif variant == VARIANTS[1]:
                row = back_index
                back_index -= 1

            y[row] = result == SUCCESS

            for col, (name, type_name) in enumerate(self.schema.items()):
                try:
                    X[row, col] = self._interpret_with_type(type_name, obj[name], name)
                except KeyError:
                    raise SchemaViolationError(f"Required field {name} is missing from data")

        variant_boundary = front_index
        y_a, y_b = y[:variant_boundary], y[variant_boundary:]
        return {
            VARIANTS[0]: (X[:variant_boundary], y[:variant_boundary]),
            VARIANTS[1]: (X[variant_boundary:], y[variant_boundary:])
        }
