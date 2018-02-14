from chain import Chain
from block import Block, create_first_block
from flask import Flask

import json
import datetime as date
import hashlib

node = Flask(__name__)
local_chain = Chain([])
local_chain.load()

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
    python_blocks = []
    for block in local_chain.blocks:
        python_blocks.append(block.to_dict())
    json_blocks = json.dumps(python_blocks)
    return json_blocks


@node.route('/mine', methods=['GET'])
def mine():
    if len(local_chain.blocks) == 0:
        # The chain is empty.
        new_block = create_first_block()
    else:
        new_block = mine_from(local_chain.blocks[-1])
    new_block.self_save()
    local_chain.add_block(new_block)
    return json.dumps(new_block.to_dict())

# The index page for convenience.
@node.route('/', methods=['GET'])
def index():
    response = "<p><a href='/chain'>chain</a></p>" + \
               "<p><a href='/mine'>mine</a></p>"
    return response, 200

if __name__ == '__main__':
    node.run()
