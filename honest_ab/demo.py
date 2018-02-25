from random import random
import numpy as np
from uuid import uuid4
from collections import defaultdict
import re
import json

from .database import *
from .redis import rd
from .facades import ExperimentResults
from .experiment_constants import *
from .models import User, Experiment
from .schema import Schema, InvalidSchemaError
from .writeahead import write_data_point_json
from .experiment_state import SerializedExperimentState

class DemoResults(object):

    @staticmethod
    def find_by_id(id):
        print_schema = json.loads(rd.get(f"demo:{id}:print_schema"))
        eid = rd.get(f"demo:{id}:eid").decode('utf-8')
        base_rates = [
            rd.get(f"demo:{id}:a_base_rate").decode("utf-8"),
            rd.get(f"demo:{id}:b_base_rate").decode("utf-8"),
        ]
        return DemoResults(eid, print_schema, base_rates)

    @staticmethod
    def generate(experiment_uuid_hex, schema_dict, print_correlation_dict, base_rates):
        results_id = uuid4().hex

        print_schema_json = json.dumps({
            name: [typ, cor_a, cor_b]
            for ((name, typ), (_, (cor_a, cor_b))) in zip(
                sorted(schema_dict.items()),
                sorted(print_correlation_dict.items())
            )
        })

        rd.set(f"demo:{results_id}:print_schema", print_schema_json)
        rd.set(f"demo:{results_id}:eid", experiment_uuid_hex)

        rd.set(f"demo:{results_id}:a_base_rate", base_rates[0])
        rd.set(f"demo:{results_id}:b_base_rate", base_rates[1])

        return results_id

    def __init__(self, experiment_uuid_hex, print_schema, base_rates):
        self.eid = experiment_uuid_hex
        self.print_schema = print_schema
        self.base_rates = base_rates

    def experiment_facade(self):
        return ExperimentResults(self.eid)

    def demo_schema(self):
        return self.print_schema

    def demo_schema_header(self):
        return ["Name", "Type", "A Correlation", "B Correlation"]

def _parse_feature_responses_from_form(form_fields):
    names = dict()
    correlations = defaultdict(lambda: dict(A=None, B=None))
    for form_key, value in form_fields.items():
        name_match = re.match("^schema_field_(\d+)_name", form_key)
        correlation_match = re.match("^schema_field_(\d+)_correlation_(A|B)", form_key)
        if name_match:
            schema_id = name_match.group(1)
            names[schema_id] = value
        elif correlation_match:
            schema_id, variant = correlation_match.group(1, 2)
            correlations[schema_id][variant] = value

    response_schema = dict()
    print_schema = dict()
    for s_id, name in names.items():
        responses = []
        print_correlations = []
        for variant, response_code in sorted(correlations[s_id].items()):
            try:
                response_func, print_correlation = Responses.parse_response_code(response_code)
                responses.append(response_func)
                print_correlations.append(print_correlation)
            except ValueError:
                raise InvalidSchemaError("Please fill in all schema fields including correlation responses.")

        response_schema[name] = responses
        print_schema[name] = print_correlations

    return response_schema, print_schema

class Demo(object):

    N_VISITORS = 1200

    @staticmethod
    @db_session
    def initialize_from_form(form_fields):
        demo_id = uuid4()
        exp = Experiment(
            name=f"Demo {demo_id} Experiment",
            description=f"Experiment for Demo {demo_id}",
            user=User.demo_user()
        )
        exp.flush()
        eid = exp.get_pk().hex

        variant_base_rates = [
            float(form_fields[f"variant_{variant}_base_rate"])
            for variant in VARIANTS
        ]

        schema = Schema.initialize_from_form(eid, form_fields)
        SerializedExperimentState.initialize(eid)

        feature_responses, pretty_responses = _parse_feature_responses_from_form(form_fields)

        if set(schema.as_dict().keys()) != set(feature_responses.keys()):
            raise InvalidSchemaError("Please fill in all schema fields including correlation responses.")

        return Demo(demo_id, schema, variant_base_rates, feature_responses, pretty_responses, eid)

    def __init__(self, demo_id, schema, variant_base_rates, correlation_responses, pretty_responses, experiment_uuid_hex):
        self.schema = schema
        self.variant_base_rates = variant_base_rates
        self.responses_by_feature = correlation_responses
        self.pretty_responses = pretty_responses
        self.eid = experiment_uuid_hex

    def run(self):
        features = []
        for name in self.schema.as_dict().keys():
            responses = self.responses_by_feature[name]
            features.append(Feature(name, 1, responses))

        pop = ExperimentPopulation(
            features=features,
            variant_base_rates=self.variant_base_rates
        )

        for _ in range(self.N_VISITORS):
            visitor = pop.sample_visitor()
            if random() < 0.5:
                variant_idx = 0
            else:
                variant_idx = 1

            did_click = visitor.react_to_variant(variant_idx)
            input_point = visitor.get_input_point()

            self._add_result(input_point, variant_idx, did_click)

        return DemoResults.generate(self.eid, self.schema.as_dict(), self.pretty_responses, self.variant_base_rates)

    def _add_result(self, input_point, variant_idx, did_click):
        variant = VARIANTS[variant_idx]
        outcome = SUCCESS if did_click else FAILURE
        encoded = self.schema.encode_input_point(input_point, variant, outcome)
        data_point_json = json.dumps(encoded)

        write_data_point_json(self.eid, data_point_json)

class Responses(object):

    @staticmethod
    def parse_response_code(code):
        if code is None or len(code) != 2:
            raise ValueError()

        sign = code[0]
        if sign == "+":
            sign_handler = lambda x: x
            name = "Positive "
        elif sign == "-":
            sign_handler = lambda x: (1 - x)
            name = "Negative "
        else:
            raise ValueError()

        response = code[1]
        if response == "n":
            response_handler = lambda x: 3 * x**2
            name += "Nonlinear"
        elif response == "l":
            response_handler = lambda x: 2 * x
            name += "Linear"
        elif response == "i":
            response_handler = lambda x: 1
            name = "Independent"
        else:
            raise ValueError()

        return lambda x: response_handler(sign_handler(x)), name

class Feature(object):

    def __init__(self, name, f_range, response_functions):
        self.name = name
        self.range = f_range
        self.responses = {
            variant: response
            for (variant, response) in enumerate(response_functions)
        }

    def response(self, normalized_feature, variant):
        return self.responses[variant](normalized_feature)

class ExperimentPopulation(object):

    def __init__(self, features, variant_base_rates):
        self.features = features
        self.variant_base_rates = variant_base_rates

    def sample_visitor(self):
        return Visitor(self.features, self.variant_base_rates)

class Visitor(object):

    def __init__(self, features, variant_base_rates):
        self.features = features
        self.variant_base_rates = variant_base_rates
        self.normalized_visitor_point = [self._uniform() for _ in self.features]

    def _uniform(self):
        return random()

    def _bernouli(self, true_rate):
        return self._uniform() < true_rate

    def r(self, point, variant):
        return np.array([self.features[i].response(p_i, variant) for i, p_i in enumerate(point)])

    def I(self, point, variant):
        return self.variant_base_rates[variant] * self.r(point, variant)

    def react_to_variant(self, variant):
        click_chance = self.I(self.normalized_visitor_point, variant).mean()
        return self._bernouli(click_chance)

    def get_input_point(self):
        return {
            feature.name: feature.range * norm
            for (feature, norm) in zip(self.features, self.normalized_visitor_point)
        }
