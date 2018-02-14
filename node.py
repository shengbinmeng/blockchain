from block import Block
from flask import Flask
from block import create_first_block

import os
import json
import datetime as date
import hashlib

node = Flask(__name__)

def sync():
    node_blocks = []
    # We're assuming that the folder and at least initial block exists
    chaindata_dir = 'chaindata'
    if os.path.exists(chaindata_dir):
        for filename in os.listdir(chaindata_dir):
            if filename.endswith('.json'):
                filepath = '%s/%s' % (chaindata_dir, filename)
                with open(filepath, 'r') as block_file:
                    block_info = json.load(block_file)
                    block_object = Block(block_info)
                    node_blocks.append(block_object)
    return node_blocks


NUM_ZEROS = 2


def generate_header(index, prev_hash, data, timestamp, nonce):
    return str(index) + prev_hash + data + str(timestamp) + str(nonce)


def calculate_hash(index, prev_hash, data, timestamp, nonce):
    header_string = generate_header(index, prev_hash, data, timestamp, nonce)
    sha = hashlib.sha256()
    sha.update(header_string.encode())
    return sha.hexdigest()

def mine_from(last_block):
    index = int(last_block.index) + 1
    timestamp = date.datetime.now()
    data = "Block #%s" % (int(last_block.index) + 1)  # random string for now, not transactions
    prev_hash = last_block.hash
    nonce = 0

    block_hash = calculate_hash(index, prev_hash, data, timestamp, nonce)
    while str(block_hash[0:NUM_ZEROS]) != '0' * NUM_ZEROS:
        nonce += 1
        block_hash = calculate_hash(index, prev_hash, data, timestamp, nonce)

    # dictionary to create the new block object.
    block_data = {}
    block_data['index'] = index
    block_data['prev_hash'] = last_block.hash
    block_data['timestamp'] = timestamp
    block_data['data'] = data
    block_data['hash'] = block_hash
    block_data['nonce'] = nonce
    return Block(block_data)


@node.route('/chain', methods=['GET'])
def chain():
    node_blocks = sync()  # update if they've changed
    # Convert our blocks into dictionaries
    # so we can send them as json objects later
    python_blocks = []
    for block in node_blocks:
        python_blocks.append(block.__dict__())
    json_blocks = json.dumps(python_blocks)
    return json_blocks


@node.route('/mine', methods=['GET'])
def mine():
    node_blocks = sync()  # gather last node
    if len(node_blocks) == 0:
        # The chain is empty.
        new_block = create_first_block()
    else:
        new_block = mine_from(node_blocks[-1])
    new_block.self_save()
    return json.dumps(new_block.__dict__())

# The index page for convenience.
@node.route('/', methods=['GET'])
def index():
    response = "<p><a href='/chain'>chain</a></p>" + \
               "<p><a href='/mine'>mine</a></p>"
    return response, 200

if __name__ == '__main__':
    node.run()