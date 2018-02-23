import os
import numpy as np

from .config import config
from .redis import rd, rd_experiment_key
from .experiment_state import SerializedExperimentState
from .schema import Schema
from .stats.discriminitive_features import DiscriminitiveFeatureModel
from .stats.significance import SignificanceModel

class BatchStatisticsProcessor(object):

    def __init__(self, experiment_uuid_hex):
        self.eid = experiment_uuid_hex

    def process(self):
        print("Start Processing")
        json_batch = self._pop_batch()
        schema = Schema.for_experiment(self.eid)
        batches_by_variant = schema.encode_batch_by_variant_with_bias(json_batch)

        with SerializedExperimentState(self.eid) as ex:
            SignificanceModel(ex).update(batches_by_variant)
            DiscriminitiveFeatureModel(ex).update(batches_by_variant)
        print("Done processing")

    def _pop_batch(self):
        redis_key = rd_experiment_key(self.eid, 'wal')
        with rd.pipeline() as pipe:
            pipe.multi()
            pipe.lrange(redis_key, 0, config.get('batch_size') - 1)
            pipe.ltrim(redis_key, config.get('batch_size'), -1)
            batch = pipe.execute()[0]

        return batch
