# -*- coding: utf-8 -*-
"""
This module implements a container for the Ndata class to simplify multi experiment analyses.

@author: Sean Martin; martins7 at tcd dot ie
"""

from enum import Enum
import logging

from neurochat.nc_data import NData

# Ideas - set up a file class which stores where the filenames are
# Based on the mode being used
# Then these could be loaded on the fly

# If this is done I could set up child classes for each of the modes, then based
# on the class I could then load appropriately when doing this
# I could even call file.load with a data object passed in
# So that memory can be reused between ndata objects

# Could set up all the analyses to work on a list so that it is easy to work with

# And then calling container.container into these analyses would perform the calcs.

# Loading from excel file

class NDataContainer():
    def __init__(self, share_positions=False):
        """
        Bulk load nData objects

        Attributes
        ----------
        _container : List
        _file_names_dict : Dict
        _units : List
        """
        self._file_names_dict = {}
        self._units = []
        self._container = []
        self._unit_count = 0
        self._share_positions = share_positions

    class EFileType(Enum):
        Spike = 1
        Position = 2
        LFP = 3
        HDF = 4

    def get_num_data(self):
        return len(self._container)
    
    def get_file_dict(self):
        return self._file_names_dict

    def get_units(self, index=None):
        if index is None:
            return self._units
        if index >= self.get_num_data():
            logging.error("Input index to get_data out of range")
            return
        return self._units[index]

    def get_data(self, index=None):
        if index is None:
            return self._container
        if index >= self.get_num_data():
            logging.error("Input index to get_data out of range")
            return
        return self._container[index]

    def add_data(self, data):
        if isinstance(data, NData):
            self._container.append(data)
        else:
            logging.error("Adding incorrect object to data container")
            return

    def list_all_units(self):
        for data in self._container:
            print("units are {}".format(data.get_unit_list()))

    def add_files(self, f_type, descriptors):
        if isinstance(descriptors, list):
            descriptors = (descriptors, None, None)
        filenames, _, _ = descriptors
        if not isinstance(f_type, self.EFileType):
            logging.error("Parameter f_type in add files must be of EFileType")
            return

        if f_type.name == "Position" and self._share_positions and len(filenames) == 1:
            for _ in range(len(self.get_file_dict()["Spike"]) - 1):
                filenames.append(filenames[0])

        # Ensure lists are empty or of equal size    
        for l in descriptors:
            if l is not None:
                if len(l) != len(filenames):
                    logging.error(
                        "add_files called with differing number of filenames and other data"
                    )
                    return

        for idx in range(len(filenames)):
            description = []
            for el in descriptors:
                if el is not None:
                    description.append(el[idx])
                else:
                    description.append(None)
            self._file_names_dict.setdefault(
                f_type.name, []).append(description)
    
    def set_units(self, units='all'):
        self._units = []
        if units == 'all':
            for data in self.get_data():
                self._units.append(data.get_unit_list())
        elif isinstance(units, list):
            for unit in units:
                if isinstance(unit, int):
                    self._units.append([unit])
                elif isinstance(unit, list):
                    self._units.append(unit)
                else:
                    logging.error(
                        "Unrecognised type {} passed to set units".format(type(unit)))

        else:
            logging.error(
                "Unrecognised type {} passed to set units".format(type(units)))
        self._unit_count = self._count_num_units()

    def load_all_data(self):
        for key, vals in self.get_file_dict().items():
            for idx, _ in enumerate(vals):
                if idx >= self.get_num_data():
                    self.add_data(NData())

            for idx, descriptor in enumerate(vals):
                self._load(idx, key, descriptor)

    def add_files_from_excel(self, file_loc):
        pass

    def _load(self, idx, key, descriptor):
        ndata = self.get_data(idx)
        key_fn_pairs = {
            "Spike" : [
                getattr(ndata, "set_spike_file"), 
                getattr(ndata, "set_spike_name"),
                getattr(ndata, "load_spike")],
            "Position": [
                getattr(ndata, "set_spatial_file"), 
                getattr(ndata, "set_spatial_name"),
                getattr(ndata, "load_spatial")],
            "LFP": [
                getattr(ndata, "set_lfp_file"),
                getattr(ndata, "set_lfp_name"),
                getattr(ndata, "load_lfp")],
        }

        filename, objectname, system = descriptor

        if objectname is not None:
            key_fn_pairs[key][1](objectname)

        if system is not None:
            ndata.set_system(system)

        if key == "Position" and self._share_positions:
            if idx == 0:
                key_fn_pairs[key][0](filename)
                key_fn_pairs[key][2]()
            else:
                ndata.spatial = self.get_data(0).spatial
            return

        if filename is not None:
            key_fn_pairs[key][0](filename)
            key_fn_pairs[key][2]()
        
    def __repr__(self):
        string = "NData Container Object with {} objects:\nFiles are {}\nUnits are \n{}".format(
            self.get_num_data(), self.get_file_dict(), self.get_units())
        return string

    def __getitem__(self, index):
        data_index, unit_index = self._index_to_data_pos(index)
        result = self.get_data(data_index)
        result.set_unit_no(self.get_units(data_index)[unit_index])
        return result

    def __len__(self):
        return sum(self._unit_count)

    def _count_num_units(self):
        counts = []
        for unit_list in self.get_units():
            counts.append(len(unit_list))
        return counts

    def _index_to_data_pos(self, index):
        counts = self._unit_count
        if index >= len(self):
            raise IndexError
        else:
            running_sum, running_idx = 0, 0
            for count in counts:
                if index < (running_sum + count):
                    return running_idx, (index - running_sum)
                else:
                    running_sum += count
                    running_idx += 1

                
        