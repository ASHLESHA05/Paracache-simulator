from PyQt5.QtWidgets import QApplication,QHBoxLayout,QTableWidget,QTableWidgetItem, QWidget, QLabel, QPushButton, QVBoxLayout, QLineEdit, QTextEdit, QComboBox
from collections import OrderedDict
from PyQt5.QtCore import Qt

import sys
import time
import math
class CacheSimulator:
    def __init__(self, memory_size, cache_size, block_size, mapping):
        self.memory_size = memory_size
        self.cache_size = cache_size
        self.block_size = block_size
        self.cache_size = min(memory_size, cache_size)
        self.mapping = mapping
        self.cache = OrderedDict()
        self.hits = 0
        self.misses = 0
        self.associativity = 2
        self.evictions = 0
        self.hit_instructions = []
        self.miss_instructions = []
        self.sample_text = ""
        self.current_text=""

    def access_memory_address(self, address):
        index, tag = self.get_index_and_tag(address)
        if address < 0 or address >= self.memory_size:
            raise ValueError(f"Invalid memory address: {hex(address)}")
        if self.mapping == "Direct Mapped":
            if index in self.cache and self.cache[index] == tag:
                self.hits += 1
                self.current_text=f'{hex(address)}: {"Hit"}\n'
                self.sample_text += f'{hex(address)}: {"Hit"}\n'
                self.hit_instructions.append(address)
            else:
                self.misses += 1
                self.current_text=f'{hex(address)}: {"Miss"}\n'
                self.sample_text += f'{hex(address)}: {"Miss"}\n'
                self.miss_instructions.append(address)
                if len(self.cache) >= self.cache_size // self.block_size:
                    self.evictions += 1
                    self.cache.popitem(last=False)
                self.cache[index] = tag

        elif self.mapping == "Set Associative":
            self.num_sets = self.cache_size // (self.block_size * self.associativity)
            set_index = index % self.num_sets
            if set_index not in self.cache:
                self.cache[set_index] = {}
            if tag in self.cache[set_index]:
                self.hits += 1
                self.current_text=f'{hex(address)}: {"Hit"}\n'
                self.sample_text += f'{hex(address)}: {"Hit"}\n'
                self.hit_instructions.append(address)
            else:
                self.misses += 1
                self.current_text=f'{hex(address)}: {"Miss"}\n'
                self.sample_text += f'{hex(address)}: {"Miss"}\n'
                self.miss_instructions.append(address)
                if len(self.cache[set_index]) >= self.associativity:
                    self.evictions += 1
                    self.cache[set_index].popitem(last=False)
                self.cache[set_index][tag] = address

        elif self.mapping == "Associative":
            if tag in self.cache.values():
                self.hits += 1
                self.current_text=f'{hex(address)}: {"Hit"}\n'
                self.sample_text += f'{hex(address)}: {"Hit"}\n'
                self.hit_instructions.append(address)
            else:
                self.misses += 1
                self.current_text=f'{hex(address)}: {"Miss"}\n'
                self.sample_text += f'{hex(address)}: {"Miss"}\n'
                self.miss_instructions.append(address)
                if len(self.cache) >= self.cache_size // self.block_size:
                    self.evictions += 1
                    self.cache.popitem(last=False)

                self.cache[address] = tag

    def get_index_and_tag(self, address):
        offset_bits = len(bin(self.block_size - 1)[2:])
        index_bits = len(bin(self.cache_size // self.block_size - 1)[2:])
        tag_bits = 32 - index_bits - offset_bits

        tag = address >> (index_bits + offset_bits)
        index = (address >> offset_bits) & ((1 << index_bits) - 1)

        return index, tag


class CacheSimulatorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.memory_sequence_text = ""  
        self.k = 0
        self.address_sequence = []
        self.cache_size = 0
        self.memory_size = 0
        self.cache_simulator=None
    def initUI(self):
        self.setWindowTitle('Cache Simulator')
        self.setGeometry(100, 100, 600, 400)
        
        # Labels and input fields
        self.memory_size_label = QLabel('Memory Size (bytes):')
        self.memory_size_input = QLineEdit()
        self.memory_size_input.setText("256")
        
        self.cache_size_label = QLabel('Cache Size (bytes):')
        self.cache_size_input = QLineEdit()
        self.cache_size_input.setText("32")
        
        self.block_size_label = QLabel('Block Size (bytes):')
        self.block_size_input = QLineEdit()
        self.block_size_input.setText("4")
        
        self.mapping_label = QLabel('Mapping Technique:')
        self.mapping_combobox = QComboBox()
        self.mapping_combobox.addItems(["Direct Mapped", "Set Associative", "Associative"])  # Add more options here
        
        self.address_label = QLabel('Memory Address Sequence:')
        self.address_input = QLineEdit()
        self.address_input.setText("11, 11, 11, 12, 13, 15, 21, 29, 56, 57")
        
        self.simulate_button = QPushButton('Simulate')
        self.simulate_button.clicked.connect(self.simulate)



        self.result_label = QLabel('')
        self.result_textbox = QTextEdit()
        self.result_textbox.setReadOnly(True)

        # Main layout
        layout = QVBoxLayout()

        # Add labels and input fields to the main layout
        layout.addWidget(self.memory_size_label)
        layout.addWidget(self.memory_size_input)
        layout.addWidget(self.cache_size_label)
        layout.addWidget(self.cache_size_input)
        layout.addWidget(self.block_size_label)
        layout.addWidget(self.block_size_input)
        layout.addWidget(self.mapping_label)
        layout.addWidget(self.mapping_combobox)
        layout.addWidget(self.address_label)
        layout.addWidget(self.address_input)
        layout.addWidget(self.simulate_button)
        layout.addWidget(self.result_label)
        layout.addWidget(self.result_textbox)

        # Create cache table
        self.cache_table = QTableWidget()

        # Create instruction table
        self.instr_table = QTableWidget()

        # Create widget for display
        self.display_widget = QWidget()
        self.display_layout = QVBoxLayout()  # QVBoxLayout for display widget
        self.hitMiss = QTextEdit()  # QTextEdit for Hit/Miss display

        self.next_button = QPushButton('next')
        self.next_button.clicked.connect(self.check)
        self.next_button.setEnabled(False)
        self.next_button.setFixedSize(100, 40)

        self.hitMiss.setPlainText("Hit / miss:")  # Initial text for Hit/Miss display
        self.display_layout.addWidget(self.hitMiss)  # Add Hit/Miss QTextEdit to display layout
        self.display_layout.addWidget(self.next_button)
        self.display_widget.setLayout(self.display_layout)  # Set layout for display widget
        self.hitMiss.setReadOnly(True)
        # Layout for tables and display widget
        layout_tables = QHBoxLayout()
        layout_tables.addWidget(self.cache_table)
        
        layout_display = QVBoxLayout()
        layout_display.addWidget(self.instr_table)
        layout_display.addWidget(self.display_widget)

        layout_tables.addLayout(layout_display)

        # Add tables and display widget layout to the main layout
        layout.addLayout(layout_tables)

        self.setLayout(layout)

        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
            }
            QLabel {
                color: #333;
                font-size: 14px;
            }
            QPushButton {
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 8px 12px;
                text-align: center;
                text-decoration: none;
                font-size: 14px;
                margin: 4px 2px;
                border-radius: 4px;
            }
            QLineEdit, QTextEdit, QComboBox {
                background-color: #ffffff;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 14px;
            }
        """)

    def check(self):
        print(self.address_sequence)
        if self.k < len(self.address_sequence):
            address=self.address_sequence[self.k]
            self.k+=1
            self.cache_simulator.access_memory_address(address)
            self.memory_sequence_text += f'{hex(address)}\n'
            self.fill_cache_table(self.cache_simulator,address,self.cache_size,self.memory_size)
            self.fill_instr_table(self.cache_simulator,address,self.cache_size,self.memory_size)
            res=self.cache_simulator.current_text
            text="Hit/Miss:\n"+res
            if(res.split(":")[1]=="miss"):
                self.hitMiss.setStyleSheet("color: red;")  # Set text color to red
            else:
                self.hitMiss.setStyleSheet("color: blue;")   
                
            self.hitMiss.setPlainText(text)
            #do
        else:
            print("reached end of sequence",self.k)
            self.next_button.setEnabled(False)
            self.hitMiss.setPlainText("reached end of sequnce ")
            self.result_label.setText('Simulation Result:')
            total_accesses = self.cache_simulator.hits + self.cache_simulator.misses
            hit_percentage = (self.cache_simulator.hits / total_accesses) * 100 if total_accesses > 0 else 0
            miss_percentage = (self.cache_simulator.misses / total_accesses) * 100 if total_accesses > 0 else 0
            result_text = f'Hits: {self.cache_simulator.hits} ({hit_percentage:.2f}%)\n'
            result_text += f'Misses: {self.cache_simulator.misses} ({miss_percentage:.2f}%)\n'
            result_text += f'Evictions: {self.cache_simulator.evictions}\n'
            result_text += 'Cache Contents:\n'
            for index, tag in self.cache_simulator.cache.items():
                result_text += f'Index: {index}, Tag: {tag}\n'
            result_text += '\nMemory Accesses:\n'
            result_text += self.cache_simulator.sample_text
            result_text += self.memory_sequence_text
            self.result_textbox.setPlainText(result_text)

    def simulate(self):
        try:
            self.next_button.setEnabled(True)
            self.k=0
            self.memory_size = int(self.memory_size_input.text())
            self.cache_size = int(self.cache_size_input.text())
            block_size = int(self.block_size_input.text())
            self.create_cache_table(self.memory_size,self.cache_size,block_size)
            self.create_instr_table(self.memory_size,self.cache_size,block_size)
    
            mapping = self.mapping_combobox.currentText()
            self.address_sequence = [int(x.strip(), 16) for x in self.address_input.text().split(',') if x.strip()]

            if not self.memory_size or not self.cache_size or not block_size or not self.address_sequence:
                self.result_label.setText('Please fill all fields')
                return

            self.cache_simulator = CacheSimulator(self.memory_size, self.cache_size, block_size, mapping)

            self.memory_sequence_text = '\n*********************************\nMemory Address Sequence:\n'

            #when next button is pressed fill the table and tell Hit or miss
            
            self.check()
             
    

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.result_textbox.setPlainText(str(e))
            exit(0)

    def create_instr_table(self,memory_size,cache_size,block_size):
        self.instr_table.setRowCount(2)
        self.instr_table.setColumnCount(3)
        self.instr_table.setHorizontalHeaderLabels(["Tag","Index","Offset"])

        block_size = int(self.block_size_input.text())
        block_offset_bits = int(block_size.bit_length()) -1
        index_bits = self.cache_table.rowCount().bit_length()-1
        tag_bit=math.log2(memory_size)-block_offset_bits-index_bits

        tag_b=QTableWidgetItem(str(int(tag_bit))+"bits")
        index_b=QTableWidgetItem(str(int(index_bits))+"bits")
        offset_b=QTableWidgetItem(str(int(block_offset_bits))+"bits")


        index_b.setFlags(index_b.flags() & ~Qt.ItemIsEditable)
        tag_b.setFlags(tag_b.flags() & ~Qt.ItemIsEditable)
        offset_b.setFlags(offset_b.flags() & ~Qt.ItemIsEditable)
        self.instr_table.setItem(0, 0, tag_b)
        self.instr_table.setItem(0, 1, index_b)
        self.instr_table.setItem(0, 2, offset_b)

        tag=QTableWidgetItem("-")
        index=QTableWidgetItem("-")
        offset=QTableWidgetItem("-")
        index.setFlags(index.flags() & ~Qt.ItemIsEditable)
        tag.setFlags(tag.flags() & ~Qt.ItemIsEditable)
        offset.setFlags(offset.flags() & ~Qt.ItemIsEditable)


        self.instr_table.setItem(1, 0, tag)
        self.instr_table.setItem(1, 1, index)
        self.instr_table.setItem(1, 2, offset)

    def create_cache_table(self,memory_size,cache_size,block_size):

        num_blocks = cache_size // block_size
        cache_table_rows = num_blocks

        self.cache_table.setRowCount(cache_table_rows)
        self.cache_table.setColumnCount(4)
        self.cache_table.setHorizontalHeaderLabels(["Index", "Valid", "Tag", "Data (hex)"])
        self.cache_table.setColumnWidth(3, 200)
        for i in range(cache_table_rows):
            index_item = QTableWidgetItem(str(i))
            valid_item = QTableWidgetItem("0")
            tag_item = QTableWidgetItem("-")
            data_item = QTableWidgetItem("0")
            index_item.setFlags(index_item.flags() & ~Qt.ItemIsEditable)
            valid_item.setFlags(valid_item.flags() & ~Qt.ItemIsEditable)
            tag_item.setFlags(tag_item.flags() & ~Qt.ItemIsEditable)
            data_item.setFlags(data_item.flags() & ~Qt.ItemIsEditable)

            self.cache_table.setItem(i, 0, index_item)
            self.cache_table.setItem(i, 1, valid_item)
            self.cache_table.setItem(i, 2, tag_item)
            self.cache_table.setItem(i, 3, data_item)
    def fill_instr_table(self,cache_simulator,address,cache_size,memory_size):
            block_size = int(self.block_size_input.text())
            block_offset_bits = int(block_size.bit_length()) -1
            index,tag=self.cache_simulator.get_index_and_tag(address)
            index_bits = self.cache_table.rowCount().bit_length()-1
            tag_bit=math.log2(memory_size)-block_offset_bits-index_bits

            tag_bit=int(tag_bit)
            index_bits=int(index_bits)

            
            try:
                bin1=str(bin(address))[2:].zfill(int(math.log2(memory_size)))
            except Exception as e:
                print("Address",address)
                print("error:",str(e))
                
                raise  ValueError(f"Invalid memory address: {hex(address)}")
            

            self.instr_table.item(1,0).setText(bin1[0:tag_bit])
            self.instr_table.item(1,1).setText(bin1[tag_bit:tag_bit+index_bits])
            self.instr_table.item(1,2).setText(bin1[tag_bit+index_bits:])
        
    def fill_cache_table(self,cache_simulator, address,cache_size,memory_size):
        try:
            index,tag=self.cache_simulator.get_index_and_tag(address)
            print(address)
            block_size = int(self.block_size_input.text())
            block_offset_bits = (block_size.bit_length() - 1)  # Number of bits needed to represent block offset
            index_bits = self.cache_table.rowCount().bit_length()-1  # Number of bits needed to represent cache index
            print("mem: ",memory_size)
            print("block: ",block_offset_bits)
            tag_bit=math.log2(memory_size)-block_offset_bits-index_bits

            if index < self.cache_table.rowCount():  # Check if index is within the range of rows in the table
                row=index
                temp=address >> block_offset_bits
                
                print("tag bit:",tag_bit)
                
                self.cache_table.item(row, 1).setText("1")
                self.cache_table.item(row, 2).setText(str(bin(tag))[2:].zfill(int(tag_bit)))
                self.cache_table.item(row, 3).setText("BLOCK "+str(hex(temp))[2:]+ " - WORD 0-"+str((cache_size//block_size)-1)) 

                # l = self.cache_simulator.current_text.split(":")
                # self.cache_table.item(row, 4).setText(l[0])
                # self.cache_table.item(row, 5).setText(l[1])  # Changed to column index 5 for HIT/MISS
        except Exception as e:
            print("Error raised", str(e))
            import traceback
            traceback.print_exc()
    
                    


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CacheSimulatorApp()
    window.setGeometry(100, 100, 600, 600)
    while True:
        window.show()
        sys.exit(app.exec_())
