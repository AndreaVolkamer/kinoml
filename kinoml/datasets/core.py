import logging
from typing import Iterable
from copy import deepcopy
from functools import wraps
from operator import attrgetter
from collections import defaultdict
import multiprocessing

import numpy as np
import pandas as pd
from tqdm.auto import tqdm

from ..core.measurements import BaseMeasurement
from ..features.core import BaseFeaturizer

logger = logging.getLogger(__name__)


class BaseDatasetProvider:
    """
    API specification for dataset providers
    """

    @classmethod
    def from_source(cls, filename=None, **kwargs):
        """
        Parse CSV/raw files to object model.
        """
        raise NotImplementedError

    def observation_model(self, backend="pytorch"):
        raise NotImplementedError

    @property
    def systems(self):
        raise NotImplementedError

    @property
    def measurement_type(self):
        raise NotImplementedError

    def measurements_as_array(self, reduce=np.mean):
        raise NotImplementedError

    def measurements_by_group(self):
        raise NotImplementedError

    @property
    def conditions(self):
        raise NotImplementedError

    def featurize(self, *featurizers: Iterable[BaseFeaturizer]):
        raise NotImplementedError

    def clear_featurizations(self):
        raise NotImplementedError

    def featurized_systems(self, key="last"):
        raise NotImplementedError

    def to_dataframe(self, *args, **kwargs):
        raise NotImplementedError

    def to_pytorch(self, **kwargs):
        raise NotImplementedError

    def to_tensorflow(self, *args, **kwargs):
        raise NotImplementedError

    def to_numpy(self, *args, **kwargs):
        raise NotImplementedError


class DatasetProvider(BaseDatasetProvider):

    """
    Base object for all DatasetProvider classes.

    Parameters:
        measurements: A DatasetProvider holds a list of `kinoml.core.measurements.BaseMeasurement`
            objects (or any of its subclasses). They must be of the same type!
    """

    _raw_data = None

    def __init__(
        self, measurements: Iterable[BaseMeasurement], *args, **kwargs,
    ):
        types = {type(measurement) for measurement in measurements}
        assert (
            len(types) == 1
        ), f"Dataset providers can only allow one type of measurement! You provided: {types}"
        self.measurements = measurements

    def __len__(self):
        return len(self.measurements)

    @classmethod
    def from_source(cls, filename=None, **kwargs):
        """
        Parse CSV/raw file to object model. This method is responsible of generating
        the objects for `self.data` and `self.measurements`, if relevant.
        Additional kwargs will be passed to `__init__`
        """
        raise NotImplementedError

    def featurize(self, *featurizers: Iterable[BaseFeaturizer], processes=1, chunksize=1):
        """
        Given a collection of `kinoml.features.core.BaseFeaturizers`, apply them
        to the systems present in the `self.measurements`.

        Parameters:
            featurizers: Featurization schemes that will be applied to the systems,
                in a stacked way.

        !!! todo
            * This function can be easily parallelized, and is often the bottleneck!
            * Shall we modify the system in place (default now), return the modified copy or store it?
        """
        systems = self.systems
        for featurizer in featurizers:
            # .supports() will test for system type, type of components, type of measurement, etc
            featurizer.supports(next(iter(systems)), raise_errors=True)

        with multiprocessing.Pool(processes=processes) as pool:
            new_featurizations = list(
                tqdm(
                    pool.imap(self._featurize_one, ((featurizers, s) for s in systems), chunksize),
                    total=len(systems),
                )
            )

        for system, featurizations in zip(systems, new_featurizations):
            system.featurizations.update(featurizations)

        invalid = sum(1 for system in systems if "failed" in system.featurizations)
        if invalid:
            logger.warning(
                "There were %d systems that could not be featurized! "
                "Check `system.featurizations['failed']` for more info.",
                invalid,
            )
        return systems

    @staticmethod
    def _featurize_one(featurizers_and_system):
        featurizers, system = featurizers_and_system
        try:
            for featurizer in featurizers:
                featurizer.featurize(system, inplace=True)
            system.featurizations["last"] = system.featurizations[featurizers[-1].name]
        except Exception as exc:
            system.featurizations["failed"] = [featurizers, exc]
        return system.featurizations

    def clear_featurizations(self):
        for system in self.systems:
            system.featurizations.clear()

    def featurized_systems(self, key="last"):
        return [ms.system.featurizations[key] for ms in self.measurements]

    def _to_dataset(self, style="pytorch"):
        """
        Generate a clean <style>.data.Dataset object for further steps
        in the pipeline (model building, etc).

        !!! Note
            This step is lossy because the resulting objects will no longer
            hold chemical data. Operations depending on such information,
            must be performed first.

        __Examples__

        ```python
        >>> provider = DatasetProvider()
        >>> provider.featurize()  # optional
        >>> splitter = TimeSplitter()
        >>> split_indices = splitter.split(provider.data)
        >>> dataset = provider.to_dataset("pytorch")  # .featurize() under the hood
        >>> X_train, X_test, y_train, y_test = train_test_split(dataset, split_indices)
        ```
        """
        raise NotImplementedError

    def to_dataframe(self, *args, **kwargs):
        """
        Generates a `pandas.DataFrame` containing information on the systems
        and their measurements

        Returns:
            pandas.DataFrame
        """
        if not self.systems:
            return pd.DataFrame()
        columns = ["Systems", "n_components", self.measurements[0].__class__.__name__]
        records = [
            (
                measurement.system.name,
                len(measurement.system.components),
                measurement.values.mean(),
            )
            for measurement in self.measurements
        ]

        return pd.DataFrame.from_records(records, columns=columns)

    def to_pytorch(self, featurizer=None, **kwargs):
        from .torch_datasets import TorchDataset, PrefeaturizedTorchDataset

        if featurizer is not None:
            return TorchDataset(
                [ms.system for ms in self.measurements],
                self.measurements_as_array(**kwargs),
                featurizer=featurizer,
                observation_model=self.observation_model(backend="pytorch"),
            )
        # else
        return PrefeaturizedTorchDataset(
            self.featurized_systems(),
            self.measurements_as_array(**kwargs),
            observation_model=self.observation_model(backend="pytorch"),
        )

    def to_xgboost(self, **kwargs):
        from xgboost import DMatrix

        dmatrix = DMatrix(
            np.asarray(self.featurized_systems()), self.measurements_as_array(**kwargs)
        )
        ## TODO: Uncomment when XGB observation models are implemented
        # dmatrix.observation_model = self.observation_model(backend="xgboost", loss="mse")
        return dmatrix

    def to_tensorflow(self, *args, **kwargs):
        raise NotImplementedError

    def to_numpy(self, *args, **kwargs):
        raise NotImplementedError

    def observation_model(self, **kwargs):
        """
        Draft implementation of a modular observation model, based on individual contributions
        from different measurement types.
        """
        return self.measurement_type.observation_model(**kwargs)

    @property
    def systems(self):
        return list({ms.system for ms in self.measurements})

    @property
    def measurement_type(self):
        return type(self.measurements[0])

    def measurements_as_array(self, reduce=np.mean):
        result = np.empty(len(self.measurements))
        for i, measurement in enumerate(self.measurements):
            result[i] = reduce(measurement.values)
        return result

    def split_by_groups(self) -> dict:
        """
        If a `kinoml.datasets.groups` class has been applied to this instance,
        this method will create more DatasetProvider instances, one per group.


        """
        groups = defaultdict(list)
        for measurement in self.measurements:
            groups[measurement.group].append(measurement)

        datasets = {}
        for key, measurements in groups.items():
            datasets[key] = type(self)(measurements)
        return datasets

    @property
    def conditions(self):
        return {ms.conditions for ms in self.measurements}

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} with "
            f"{len(self.measurements)} {self.measurement_type.__name__} measurements "
            f"and {len(self.systems)} systems>"
        )


class MultiDatasetProvider(DatasetProvider):
    def __init__(self, measurements: Iterable[BaseMeasurement], *args, **kwargs):
        by_type = defaultdict(list)
        for measurement in measurements:
            by_type[type(measurement)].append(measurement)

        providers = []
        for typed_measurements in by_type.values():
            if typed_measurements:
                providers.append(DatasetProvider(typed_measurements))

        self.providers = providers

    def observation_models(self, **kwargs):
        return [p.observation_model(**kwargs) for p in self.providers]

    @property
    def measurements(self):
        """
        Note that right now we are flattening the list for API compatibility.
        With a flattened list:
        >>> lengths = [len(p) for p in providers]
        >>> first = self.measurements[:lengths[0]]
        >>> second = self.measurements[lengths[0]:lengths[0] + lengths[1]]
        With several lists:
        >>> first, second = self.measurements
        """
        return [ms for prov in self.providers for ms in prov.measurements]

    def indices_by_provider(self):
        indices = {}
        offset = 0
        for p in self.providers:
            indices[p.measurement_type] = slice(offset, offset + len(p.measurements))
            offset += len(p.measurements)
        return indices

    def to_dataframe(self, *args, **kwargs):
        columns = ["Systems", "n_components", "Measurement", "MeasurementType"]
        records = []
        for provider in self.providers:
            measurement_type = provider.measurement_type.__name__
            for measurement in provider.measurements:
                records.append(
                    (
                        measurement.system.name,
                        len(measurement.system.components),
                        measurement.values.mean(),
                        measurement_type,
                    )
                )

        return pd.DataFrame.from_records(records, columns=columns)

    def to_pytorch(self, **kwargs):
        return [p.to_pytorch(**kwargs) for p in self.providers]

    def to_xgboost(self, **kwargs):
        return [p.to_xgboost(**kwargs) for p in self.providers]


class ProteinLigandDatasetProvider(DatasetProvider):
    pass
