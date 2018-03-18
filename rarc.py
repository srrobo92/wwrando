
from dzx import DZx
from events import EventList
from fs_helpers import *
from io import BytesIO

class RARC:
  def __init__(self, file_path):
    self.file_path = file_path
    
    with open(self.file_path, "rb") as file:
      self.data = BytesIO(file.read())
    
    data = self.data
    
    self.file_data_list_offset = read_u32(data, 0xC) + 0x20
    num_nodes = read_u32(data, 0x20)
    node_list_offset = 0x40
    file_entries_list_offset = read_u32(data, 0x2C) + 0x20
    self.string_list_offset = read_u32(data, 0x34) + 0x20
    
    self.dzx_files = []
    self.event_list_files = []
    for node_index in range(0, num_nodes):
      node_offset = node_list_offset + node_index*0x10
      node_name = read_str(data, node_offset, 4)
      
      num_files_in_node = read_u16(data, node_offset + 0xA)
      first_file_index_in_node = read_u32(data, node_offset + 0xC)
      for file_index in range(first_file_index_in_node, first_file_index_in_node+num_files_in_node):
        file_entry_offset = file_entries_list_offset + file_index*0x14
        
        file_entry = FileEntry(data, file_entry_offset, self)
        
        if file_entry.id == 0xFFFF:
          continue
        
        if file_entry.name.endswith(".dzs"):
          pass
          dzx = DZx(file_entry)
          self.dzx_files.append(dzx)
        elif file_entry.name.endswith(".dzr"):
          pass
          dzx = DZx(file_entry)
          self.dzx_files.append(dzx)
        elif file_entry.name == "event_list.dat":
          event_list = EventList(file_entry)
          self.event_list_files.append(event_list)
  
  def save_to_disk(self):
    for dzx in self.dzx_files:
      self.data.seek(dzx.file_entry.data_offset + self.file_data_list_offset)
      dzx.file_entry.data.seek(0)
      self.data.write(dzx.file_entry.data.read())
    
    for event_list in self.event_list_files:
      self.data.seek(event_list.file_entry.data_offset + self.file_data_list_offset)
      event_list.file_entry.data.seek(0)
      self.data.write(event_list.file_entry.data.read())
    
    with open(self.file_path, "wb") as file:
      self.data.seek(0)
      file.write(self.data.read())

class FileEntry:
  def __init__(self, data, offset, rarc):
    self.id = read_u16(data, offset)
    self.name_offset = read_u16(data, offset + 6)
    self.data_offset = read_u32(data, offset + 8)
    self.data_size = read_u32(data, offset + 0xC)
    self.name = read_str_until_null_character(data, self.name_offset+rarc.string_list_offset)
    
    if self.data_offset == 0xFFFFFFFF:
      self.data = None
    else:
      data.seek(self.data_offset+rarc.file_data_list_offset)
      self.data = BytesIO(data.read(self.data_size))