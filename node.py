from chain import Chain
from block import Block, create_first_block
from flask import Flask

import json
import datetime as date
import hashlib
import requests

node = Flask(__name__)
local_chain = Chain([])
local_chain.load()

NUM_ZEROS = 2
PEERS = [
    'http://localhost:5000',
    'http://localhost:5001',
    'http://localhost:5002',
    'http://localhost:5003',
]


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


def sync_overall(peers, save=False):
    best_chain = local_chain
    for peer in peers:
        # try to connect to peer
        peer_chain_url = peer + '/chain'
        try:
            r = requests.get(peer_chain_url, timeout=5)
            peer_chain_dict = r.json()
            peer_blocks = [Block(block_dict) for block_dict in peer_chain_dict]
            peer_chain = Chain(peer_blocks)

            if peer_chain.is_valid() and peer_chain > best_chain:
                best_chain = peer_chain

        except requests.exceptions.ConnectionError:
            print("Peer at %s not running. Continuing to next peer." % peer)
        except requests.exceptions.Timeout:
            print("Timeout when connecting peer at %s." % peer)
        else:
            print("Peer at %s is running. Gathered their blochchain for analysis." % peer)
    print("Longest blockchain has %s blocks" % len(best_chain))

    # for now, save the new blockchain over whatever was there
    if save:
        best_chain.save()
    return best_chain


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


@node.route('/sync', methods=['GET'])
def sync():
    best_chain = sync_overall(PEERS, True)
    response = "Done."
    if best_chain > local_chain:
        response += " Local chain is updated, max index %d => %d." % (local_chain.max_index(), best_chain.max_index())
        local_chain.load()
    else:
        response += " Local chain is not updated."
    return response

# The index page for convenience.
@node.route('/', methods=['GET'])
def index():
    response = "<p><a href='/chain'>chain</a></p>" + \
               "<p><a href='/mine'>mine</a></p>" + \
                "<p><a href='/sync'>sync</a></p>"
    return response, 200

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    parser.add_argument('-n', '--node', default="default_node_id", type=str, help='id of this node')
    args = parser.parse_args()
    port = args.port
    node_identifier = args.node
    print("node id: " + node_identifier)
    node.run(host='0.0.0.0', port=port)
