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

from behave import fixture
from inat_to_cams import cams_interface, cams_reader, cams_writer, synchronise_inat_to_cams


@fixture
def before_all(context):
    context.writer = cams_writer.CamsWriter()
    context.reader = cams_reader.CamsReader()
    context.synchroniser = synchronise_inat_to_cams.synchroniser
    context.connection = cams_interface.connection
    context.connection.delete_rows_with_inat_ref_of_length(4)
    # logging.basicConfig(filename="error.log")
