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

from enum import Enum
from typing import Final

from opensafely._vendor.deprecated import deprecated

ERROR_TYPE: Final = "error.type"
"""
Deprecated in favor of stable :py:const:`opentelemetry.semconv.attributes.error_attributes.ERROR_TYPE`.
"""


@deprecated(
    reason="Deprecated in favor of stable :py:const:`opentelemetry.semconv.attributes.error_attributes.ErrorTypeValues`."
)  # type: ignore
class ErrorTypeValues(Enum):
    OTHER = "_OTHER"
    """Deprecated in favor of stable :py:const:`opentelemetry.semconv.attributes.error_attributes.ErrorTypeValues.OTHER`."""
