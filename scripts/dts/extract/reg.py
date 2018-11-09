#
# Copyright (c) 2018 Bobby Noelte
#
# SPDX-License-Identifier: Apache-2.0
#

from extract.globals import *
from extract.directive import DTDirective
from extract.edts import *

##
# @brief Manage reg directive.
#
class DTReg(DTDirective):

    def __init__(self):
        pass

    ##
    # @brief Populate EDTS register information
    #
    # @param node_address Address of node owning the
    #                     reg definition.
    #
    def populate_edts(self, node_address):

        device_id = edts_device_id(node_address)
        node = reduced[node_address]

        try:
            reg = reduced[node_address]['props']['reg']
        except:
            return

        try:
            names = node['props']['reg-names']
            if type(names) is not list: names = [ names, ]
        except:
            names = None

        reg = deepcopy(reg)
        # if we only have on reg we get a scalar
        if type(reg) is not list: reg = [ reg, ]

        # Newer versions of dtc might have the reg propertly look like
        # reg = <1 2>, <3 4>;
        # So we need to flatten the list in that case
        if isinstance(reg[0], list):
            reg = [item for sublist in reg for item in sublist]

        (nr_address_cells, nr_size_cells) = get_addr_size_cells(node_address)

        index = 0
        while reg:
            addr = 0
            size = 0

            for x in range(nr_address_cells):
                addr += reg.pop(0) << (32 * (nr_address_cells - x - 1))
            for x in range(nr_size_cells):
                size += reg.pop(0) << (32 * (nr_size_cells - x - 1))

            addr += translate_addr(addr, node_address,
                    nr_address_cells, nr_size_cells)

            edts_insert_device_property(device_id,
                'reg/{}/address'.format(index), addr)
            if nr_size_cells:
                edts_insert_device_property(device_id,
                    'reg/{}/size'.format(index), size)
            if names is not None:
                edts_insert_device_property(device_id,
                    'reg/{}/name'.format(index), names[index])

            index += 1

    ##
    # @brief Extract reg directive info
    #
    # @param node_address Address of node owning the
    #                     reg definition.
    # @param yaml YAML definition for the owning node.
    # @param names (unused)
    # @param def_label Define label string of node owning the
    #                  compatible definition.
    #
    def extract(self, node_address, yaml, names, def_label, div):

        node = reduced[node_address]
        node_compat = get_compat(node_address)

        reg = reduced[node_address]['props']['reg']
        if type(reg) is not list: reg = [ reg, ]

        (nr_address_cells, nr_size_cells) = get_addr_size_cells(node_address)

        # generate defines
        l_base = def_label.split('/')
        l_addr = [convert_string_to_label("BASE_ADDRESS")]
        l_size = ["SIZE"]

        index = 0
        props = list(reg)

        # Newer versions of dtc might have the reg propertly look like
        # reg = <1 2>, <3 4>;
        # So we need to flatten the list in that case
        if isinstance(props[0], list):
            props = [item for sublist in props for item in sublist]

        while props:
            prop_def = {}
            prop_alias = {}
            addr = 0
            size = 0
            # Check is defined should be indexed (_0, _1)
            if index == 0 and len(props) < 3:
                # 1 element (len 2) or no element (len 0) in props
                l_idx = []
            else:
                l_idx = [str(index)]

            try:
                name = [names.pop(0).upper()]
            except:
                name = []

            for x in range(nr_address_cells):
                addr += props.pop(0) << (32 * (nr_address_cells - x - 1))
            for x in range(nr_size_cells):
                size += props.pop(0) << (32 * (nr_size_cells - x - 1))

            addr += translate_addr(addr, node_address,
                    nr_address_cells, nr_size_cells)

            l_addr_fqn = '_'.join(l_base + l_addr + l_idx)
            l_size_fqn = '_'.join(l_base + l_size + l_idx)
            if nr_address_cells:
                prop_def[l_addr_fqn] = hex(addr)
            if nr_size_cells:
                prop_def[l_size_fqn] = int(size / div)
            if len(name):
                if nr_address_cells:
                    prop_alias['_'.join(l_base + name + l_addr)] = l_addr_fqn
                if nr_size_cells:
                    prop_alias['_'.join(l_base + name + l_size)] = l_size_fqn

            # generate defs for node aliases
            if node_address in aliases:
                for i in aliases[node_address]:
                    alias_label = convert_string_to_label(i)
                    alias_addr = [alias_label] + l_addr + l_idx
                    alias_size = [alias_label] + l_size + l_idx
                    prop_alias['_'.join(alias_addr)] = '_'.join(l_base + l_addr + l_idx)
                    prop_alias['_'.join(alias_size)] = '_'.join(l_base + l_size + l_idx)

            insert_defs(node_address, prop_def, prop_alias)

            # increment index for definition creation
            index += 1

##
# @brief Management information for registers.
reg = DTReg()
