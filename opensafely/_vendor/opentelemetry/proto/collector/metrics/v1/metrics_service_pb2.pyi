"""
@generated by mypy-protobuf.  Do not edit manually!
isort:skip_file
Copyright 2019, OpenTelemetry Authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import builtins
import collections.abc
import google.protobuf.descriptor
import google.protobuf.internal.containers
import google.protobuf.message
import opentelemetry.proto.metrics.v1.metrics_pb2
import sys

if sys.version_info >= (3, 8):
    import typing as typing_extensions
else:
    import typing_extensions

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing_extensions.final
class ExportMetricsServiceRequest(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    RESOURCE_METRICS_FIELD_NUMBER: builtins.int
    @property
    def resource_metrics(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        opentelemetry.proto.metrics.v1.metrics_pb2.ResourceMetrics
    ]:
        """An array of ResourceMetrics.
        For data coming from a single resource this array will typically contain one
        element. Intermediary nodes (such as OpenTelemetry Collector) that receive
        data from multiple origins typically batch the data before forwarding further and
        in that case this array will contain multiple elements.
        """

    def __init__(
        self,
        *,
        resource_metrics: (
            collections.abc.Iterable[
                opentelemetry.proto.metrics.v1.metrics_pb2.ResourceMetrics
            ]
            | None
        ) = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing_extensions.Literal[
            "resource_metrics", b"resource_metrics"
        ],
    ) -> None: ...

global___ExportMetricsServiceRequest = ExportMetricsServiceRequest

@typing_extensions.final
class ExportMetricsServiceResponse(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    PARTIAL_SUCCESS_FIELD_NUMBER: builtins.int
    @property
    def partial_success(self) -> global___ExportMetricsPartialSuccess:
        """The details of a partially successful export request.

        If the request is only partially accepted
        (i.e. when the server accepts only parts of the data and rejects the rest)
        the server MUST initialize the `partial_success` field and MUST
        set the `rejected_<signal>` with the number of items it rejected.

        Servers MAY also make use of the `partial_success` field to convey
        warnings/suggestions to senders even when the request was fully accepted.
        In such cases, the `rejected_<signal>` MUST have a value of `0` and
        the `error_message` MUST be non-empty.

        A `partial_success` message with an empty value (rejected_<signal> = 0 and
        `error_message` = "") is equivalent to it not being set/present. Senders
        SHOULD interpret it the same way as in the full success case.
        """

    def __init__(
        self,
        *,
        partial_success: global___ExportMetricsPartialSuccess | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing_extensions.Literal[
            "partial_success", b"partial_success"
        ],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing_extensions.Literal[
            "partial_success", b"partial_success"
        ],
    ) -> None: ...

global___ExportMetricsServiceResponse = ExportMetricsServiceResponse

@typing_extensions.final
class ExportMetricsPartialSuccess(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    REJECTED_DATA_POINTS_FIELD_NUMBER: builtins.int
    ERROR_MESSAGE_FIELD_NUMBER: builtins.int
    rejected_data_points: builtins.int
    """The number of rejected data points.

    A `rejected_<signal>` field holding a `0` value indicates that the
    request was fully accepted.
    """
    error_message: builtins.str
    """A developer-facing human-readable message in English. It should be used
    either to explain why the server rejected parts of the data during a partial
    success or to convey warnings/suggestions during a full success. The message
    should offer guidance on how users can address such issues.

    error_message is an optional field. An error_message with an empty value
    is equivalent to it not being set.
    """
    def __init__(
        self,
        *,
        rejected_data_points: builtins.int = ...,
        error_message: builtins.str = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing_extensions.Literal[
            "error_message",
            b"error_message",
            "rejected_data_points",
            b"rejected_data_points",
        ],
    ) -> None: ...

global___ExportMetricsPartialSuccess = ExportMetricsPartialSuccess
