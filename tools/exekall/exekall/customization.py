#! /usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
#
# Copyright (C) 2018, ARM Limited and contributors.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import numbers

from exekall.engine import NoValue, StorageDB
from exekall.utils import out, get_name

class AdaptorBase:
    name = 'default'

    def __init__(self, args=None):
        if args is None:
            args = dict()
        self.args = args

    def get_non_reusable_type_set(self):
        return set()

    @staticmethod
    def get_tags(value):
        if isinstance(value, numbers.Number):
            tags = {'': value}
        else:
            tags = {}
        return tags

    load_db = None

    def update_expr_data(self, expr_data):
        return

    def filter_op_pool(self, op_pool):
        return {
            op for op in op_pool
            # Only select operators with non-empty parameter list. This
            # rules out all classes __init__ that do not take parameter, as
            # they are typically not interesting to us.
            if op.get_prototype()[0]
        }

    def get_prebuilt_list(self):
        return []

    def get_hidden_callable_set(self, op_map):
        self.hidden_callable_set = set()
        return self.hidden_callable_set

    @staticmethod
    def register_cli_param(parser):
        pass

    @staticmethod
    def get_default_type_goal_pattern_set():
        return {'*Result'}

    def resolve_cls_name(self, goal):
        return utils.get_class_from_name(goal, sys.modules)

    def load_db(self, db_path):
        return StorageDB.from_path(db_path)

    def finalize_expr(self, expr):
        pass

    def result_str(self, result):
        val = result.value
        if val is NoValue or val is None:
            failed_parents = result.get_failed_expr_vals()
            for failed_parent in failed_parents:
                excep = failed_parent.excep
                return 'EXCEPTION ({type}): {msg}'.format(
                    type = get_name(type(excep)),
                    msg = excep
                )
            return 'No result computed'
        else:
            return str(val)

    def process_results(self, result_map):
        hidden_callable_set = self.hidden_callable_set

        # Get all IDs and compute the maximum length to align the output
        result_id_map = {
            result: result.get_id(
                hidden_callable_set=hidden_callable_set,
                full_qual=False,
                qual=False,
            )
            for expr, result_list in result_map.items()
            for result in result_list
        }

        max_id_len = len(max(result_id_map.values(), key=len))

        for expr, result_list in result_map.items():
            for result in result_list:
                msg = self.result_str(result)
                msg = msg + '\n' if '\n' in msg else msg
                out('{id:<{max_id_len}} {result}'.format(
                    id=result_id_map[result],
                    result=msg,
                    max_id_len=max_id_len,
                ))

    @classmethod
    def get_adaptor_cls(cls, name=None):
        subcls_list = list(cls.__subclasses__())
        if len(subcls_list) > 1 and not name:
            raise ValueError('An adaptor name must be specified if there is more than one adaptor to choose from')

        for subcls in subcls_list:
            if name:
                if subcls.name == name:
                    return subcls
            else:
                return subcls
        return None

