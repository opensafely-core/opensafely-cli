# Copyright The OpenTelemetry Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# pylint: disable=too-many-ancestors, unused-import

from logging import getLogger
from typing import Dict, Generator, Iterable, List, Optional, Union

# This kind of import is needed to avoid Sphinx errors.
import opensafely._vendor.opentelemetry.sdk.metrics
from opensafely._vendor.opentelemetry.metrics import CallbackT
from opensafely._vendor.opentelemetry.metrics import Counter as APICounter
from opensafely._vendor.opentelemetry.metrics import Histogram as APIHistogram
from opensafely._vendor.opentelemetry.metrics import ObservableCounter as APIObservableCounter
from opensafely._vendor.opentelemetry.metrics import ObservableGauge as APIObservableGauge
from opensafely._vendor.opentelemetry.metrics import (
    ObservableUpDownCounter as APIObservableUpDownCounter,
)
from opensafely._vendor.opentelemetry.metrics import UpDownCounter as APIUpDownCounter
from opensafely._vendor.opentelemetry.metrics._internal.instrument import CallbackOptions
from opensafely._vendor.opentelemetry.sdk.metrics._internal.measurement import Measurement
from opensafely._vendor.opentelemetry.sdk.util.instrumentation import InstrumentationScope

_logger = getLogger(__name__)


_ERROR_MESSAGE = (
    "Expected ASCII string of maximum length 63 characters but got {}"
)


class _Synchronous:
    def __init__(
        self,
        name: str,
        instrumentation_scope: InstrumentationScope,
        measurement_consumer: "opensafely._vendor.opentelemetry.sdk.metrics.MeasurementConsumer",
        unit: str = "",
        description: str = "",
    ):
        # pylint: disable=no-member
        result = self._check_name_unit_description(name, unit, description)

        if result["name"] is None:
            raise Exception(_ERROR_MESSAGE.format(name))

        if result["unit"] is None:
            raise Exception(_ERROR_MESSAGE.format(unit))

        name = result["name"]
        unit = result["unit"]
        description = result["description"]

        self.name = name.lower()
        self.unit = unit
        self.description = description
        self.instrumentation_scope = instrumentation_scope
        self._measurement_consumer = measurement_consumer
        super().__init__(name, unit=unit, description=description)


class _Asynchronous:
    def __init__(
        self,
        name: str,
        instrumentation_scope: InstrumentationScope,
        measurement_consumer: "opensafely._vendor.opentelemetry.sdk.metrics.MeasurementConsumer",
        callbacks: Optional[Iterable[CallbackT]] = None,
        unit: str = "",
        description: str = "",
    ):
        # pylint: disable=no-member
        result = self._check_name_unit_description(name, unit, description)

        if result["name"] is None:
            raise Exception(_ERROR_MESSAGE.format(name))

        if result["unit"] is None:
            raise Exception(_ERROR_MESSAGE.format(unit))

        name = result["name"]
        unit = result["unit"]
        description = result["description"]

        self.name = name.lower()
        self.unit = unit
        self.description = description
        self.instrumentation_scope = instrumentation_scope
        self._measurement_consumer = measurement_consumer
        super().__init__(name, callbacks, unit=unit, description=description)

        self._callbacks: List[CallbackT] = []

        if callbacks is not None:

            for callback in callbacks:

                if isinstance(callback, Generator):

                    # advance generator to it's first yield
                    next(callback)

                    def inner(
                        options: CallbackOptions,
                        callback=callback,
                    ) -> Iterable[Measurement]:
                        try:
                            return callback.send(options)
                        except StopIteration:
                            return []

                    self._callbacks.append(inner)
                else:
                    self._callbacks.append(callback)

    def callback(
        self, callback_options: CallbackOptions
    ) -> Iterable[Measurement]:
        for callback in self._callbacks:
            try:
                for api_measurement in callback(callback_options):
                    yield Measurement(
                        api_measurement.value,
                        instrument=self,
                        attributes=api_measurement.attributes,
                    )
            except Exception:  # pylint: disable=broad-except
                _logger.exception(
                    "Callback failed for instrument %s.", self.name
                )


class Counter(_Synchronous, APICounter):
    def __new__(cls, *args, **kwargs):
        if cls is Counter:
            raise TypeError("Counter must be instantiated via a meter.")
        return super().__new__(cls)

    def add(
        self, amount: Union[int, float], attributes: Dict[str, str] = None
    ):
        if amount < 0:
            _logger.warning(
                "Add amount must be non-negative on Counter %s.", self.name
            )
            return
        self._measurement_consumer.consume_measurement(
            Measurement(amount, self, attributes)
        )


class UpDownCounter(_Synchronous, APIUpDownCounter):
    def __new__(cls, *args, **kwargs):
        if cls is UpDownCounter:
            raise TypeError("UpDownCounter must be instantiated via a meter.")
        return super().__new__(cls)

    def add(
        self, amount: Union[int, float], attributes: Dict[str, str] = None
    ):
        self._measurement_consumer.consume_measurement(
            Measurement(amount, self, attributes)
        )


class ObservableCounter(_Asynchronous, APIObservableCounter):
    def __new__(cls, *args, **kwargs):
        if cls is ObservableCounter:
            raise TypeError(
                "ObservableCounter must be instantiated via a meter."
            )
        return super().__new__(cls)


class ObservableUpDownCounter(_Asynchronous, APIObservableUpDownCounter):
    def __new__(cls, *args, **kwargs):
        if cls is ObservableUpDownCounter:
            raise TypeError(
                "ObservableUpDownCounter must be instantiated via a meter."
            )
        return super().__new__(cls)


class Histogram(_Synchronous, APIHistogram):
    def __new__(cls, *args, **kwargs):
        if cls is Histogram:
            raise TypeError("Histogram must be instantiated via a meter.")
        return super().__new__(cls)

    def record(
        self, amount: Union[int, float], attributes: Dict[str, str] = None
    ):
        if amount < 0:
            _logger.warning(
                "Record amount must be non-negative on Histogram %s.",
                self.name,
            )
            return
        self._measurement_consumer.consume_measurement(
            Measurement(amount, self, attributes)
        )


class ObservableGauge(_Asynchronous, APIObservableGauge):
    def __new__(cls, *args, **kwargs):
        if cls is ObservableGauge:
            raise TypeError(
                "ObservableGauge must be instantiated via a meter."
            )
        return super().__new__(cls)


# Below classes exist to prevent the direct instantiation
class _Counter(Counter):
    pass


class _UpDownCounter(UpDownCounter):
    pass


class _ObservableCounter(ObservableCounter):
    pass


class _ObservableUpDownCounter(ObservableUpDownCounter):
    pass


class _Histogram(Histogram):
    pass


class _ObservableGauge(ObservableGauge):
    pass
