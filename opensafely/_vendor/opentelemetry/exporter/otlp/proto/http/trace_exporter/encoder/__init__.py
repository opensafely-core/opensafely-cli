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

import logging  # noqa: F401
from collections import abc  # noqa: F401
from typing import Any, List, Optional, Sequence  # noqa: F401

from opensafely._vendor.opentelemetry.proto.collector.trace.v1.trace_service_pb2 import (  # noqa: F401
    ExportTraceServiceRequest as PB2ExportTraceServiceRequest,
)
from opensafely._vendor.opentelemetry.proto.common.v1.common_pb2 import (  # noqa: F401
    AnyValue as PB2AnyValue,
)
from opensafely._vendor.opentelemetry.proto.common.v1.common_pb2 import (  # noqa: F401
    ArrayValue as PB2ArrayValue,
)
from opensafely._vendor.opentelemetry.proto.common.v1.common_pb2 import (  # noqa: F401
    InstrumentationScope as PB2InstrumentationScope,
)
from opensafely._vendor.opentelemetry.proto.common.v1.common_pb2 import (  # noqa: F401
    KeyValue as PB2KeyValue,
)
from opensafely._vendor.opentelemetry.proto.resource.v1.resource_pb2 import (  # noqa: F401
    Resource as PB2Resource,
)
from opensafely._vendor.opentelemetry.proto.trace.v1.trace_pb2 import (  # noqa: F401
    ResourceSpans as PB2ResourceSpans,
)
from opensafely._vendor.opentelemetry.proto.trace.v1.trace_pb2 import (  # noqa: F401
    ScopeSpans as PB2ScopeSpans,
)
from opensafely._vendor.opentelemetry.proto.trace.v1.trace_pb2 import (  # noqa: F401
    Span as PB2SPan,
)
from opensafely._vendor.opentelemetry.proto.trace.v1.trace_pb2 import (  # noqa: F401
    Status as PB2Status,
)
from opensafely._vendor.opentelemetry.sdk.trace import (
    Event,  # noqa: F401
    Resource,  # noqa: F401
)
from opensafely._vendor.opentelemetry.sdk.trace import Span as SDKSpan  # noqa: F401
from opensafely._vendor.opentelemetry.sdk.util.instrumentation import (  # noqa: F401
    InstrumentationScope,
)
from opensafely._vendor.opentelemetry.trace import (
    Link,  # noqa: F401
    SpanKind,  # noqa: F401
)
from opensafely._vendor.opentelemetry.trace.span import (  # noqa: F401
    SpanContext,
    Status,
    TraceState,
)
from opensafely._vendor.opentelemetry.util.types import Attributes  # noqa: F401
