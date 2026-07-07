#!/usr/bin/env python3
# DESCRIPTION: Verilator: Verilog Test driver/expect definition
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of either the GNU Lesser General Public License Version 3
# or the Perl Artistic License Version 2.0.
# SPDX-FileCopyrightText: 2026 Wilson Snyder
# SPDX-License-Identifier: LGPL-3.0-only OR Artistic-2.0

import vltest_bootstrap
import fst_scope_common

test.scenarios('vlt_all')
test.top_filename = "t/t_trace_scope_comp.v"

test.compile(verilator_flags2=['--cc', '--trace-fst'])

test.execute()

scopes = fst_scope_common.fst_scope_components(test, test.trace_filename)

expected = {
    'top': '',  # C++ model instance, has no Verilog definition
    'top.t': 't',  # Inlined into the root wrapper
    'top.t.u_mid': 'MidNoInline',  # Not inlined
    'top.t.u_mid.u_leaf': 'Leaf',  # Inlined
    'top.t.u_mid.gen_blk[0]': '',  # Generate block, has no definition name
    'top.t.u_mid.gen_blk[1]': '',
    'top.t.u_mid.gen_blk[0].u_gleaf': 'Leaf',  # Inlined under generate block
    'top.t.u_mid.gen_blk[1].u_gleaf': 'Leaf',
    'top.t.u_param': 'ParamMod',  # Parameterized; original definition name
    'top.t.the_intf': 'Intf',  # Interface
}

for path, comp in sorted(expected.items()):
    if path not in scopes:
        test.error("scope not found in FST hierarchy: " + path)
    elif scopes[path] != comp:
        test.error("scope '" + path + "' has component '" + scopes[path] + "' expected '" +
                   comp + "'")

test.passes()
