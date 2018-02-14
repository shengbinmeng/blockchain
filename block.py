import hashlib
import os
import json
import datetime as date

NUM_ZEROS = 2
BLOCK_VAR_CONVERSIONS = {'index': int, 'nonce': int, 'hash': str, 'prev_hash': str, 'timestamp': str}

class Block(object):
    def __init__(self, dictionary):
        '''
          We're looking for index, timestamp, data, prev_hash, nonce
        '''
        for key, value in dictionary.items():
            if key in BLOCK_VAR_CONVERSIONS:
                setattr(self, key, BLOCK_VAR_CONVERSIONS[key](value))
            else:
                setattr(self, key, value)

        if not hasattr(self, 'nonce'):
            # we're throwin this in for generation
            self.nonce = 'None'
        if not hasattr(self, 'hash'):  # in creating the first block, needs to be removed in future
            self.hash = self.update_self_hash()

    def header_string(self):
        return str(self.index) + self.prev_hash + self.data + str(self.timestamp) + str(self.nonce)

    def generate_header(index, prev_hash, data, timestamp, nonce):
        return str(index) + prev_hash + data + str(timestamp) + str(nonce)

    def update_self_hash(self):
        sha = hashlib.sha256()
        sha.update(self.header_string().encode())
        new_hash = sha.hexdigest()
        self.hash = new_hash
        return new_hash

    def self_save(self):
        chaindata_dir = 'chaindata'
        if not os.path.exists(chaindata_dir):
            # make chaindata dir
            os.mkdir(chaindata_dir)
        index_string = str(self.index).zfill(6)  # front of zeros so they stay in numerical order
        filename = '%s/%s.json' % (chaindata_dir, index_string)
        with open(filename, 'w') as block_file:
            json.dump(self.to_dict(), block_file)

    def to_dict(self):
        info = {}
        info['index'] = str(self.index)
        info['timestamp'] = str(self.timestamp)
        info['prev_hash'] = str(self.prev_hash)
        info['hash'] = str(self.hash)
        info['data'] = str(self.data)
        info['nonce'] = str(self.nonce)
        return info

    def is_valid(self):
        self.update_self_hash()
        if str(self.hash[0:NUM_ZEROS]) == '0' * NUM_ZEROS:
            return True
        else:
            return False

    def __str__(self):
        return "Block<prev_hash: %s,hash: %s>" % (self.prev_hash, self.hash)


def create_first_block():
    # index zero and arbitrary previous hash
    block_data = {}
    block_data['index'] = 0
    block_data['timestamp'] = date.datetime.now()
    block_data['data'] = 'Block #0'
    block_data['prev_hash'] = ''
    block_data['nonce'] = 0  # starting it at 0
    return Block(block_data)


if __name__ == '__main__':
    # check if chaindata folder exists.
    chaindata_dir = 'chaindata/'
    if not os.path.exists(chaindata_dir):
        # make chaindata dir
        os.mkdir(chaindata_dir)
    # check if dir is empty from just creation, or empty before
    if os.listdir(chaindata_dir) == []:
        # create and save first block
        first_block = create_first_block()
        first_block.save()
