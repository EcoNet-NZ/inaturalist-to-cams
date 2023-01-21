#  ====================================================================
#  Copyright 2023 EcoNet.NZ
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#  ====================================================================
import pytz
from datetime import datetime, tzinfo

date_field=1674169903
dt = datetime.fromtimestamp(date_field)
print(dt.tzinfo)
timezone = pytz.timezone('Pacific/Auckland')
localized_date = timezone.localize(dt)
print(localized_date)
print(localized_date.tzinfo)
print(localized_date.astimezone(timezone))
print(localized_date.astimezone(timezone).tzinfo)
print(dt.astimezone(timezone))
print(dt.astimezone(timezone).tzinfo)